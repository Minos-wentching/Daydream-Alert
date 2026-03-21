from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from app.core.models import FocusState, Observation, StateUpdate, TaskConfig
from app.core.state_machine import AlertPolicy, AlertStateMachine
from app.core.whitelist import is_window_allowed
from app.io.process_terminator import ProcessTerminator


@dataclass
class VisionSignals:
    face_present: bool = False
    looking_down: bool = False
    phone_present: bool = False


def _now_local() -> datetime:
    return datetime.now().astimezone()


class MonitorController:
    def __init__(
        self,
        config: TaskConfig,
        active_window_provider,
        vision_analyzer,
        on_update: Callable[[StateUpdate], None],
        process_terminator: ProcessTerminator | None = None,
    ):
        self._config = config.normalized()
        self._active_window_provider = active_window_provider
        self._vision_analyzer = vision_analyzer
        self._on_update = on_update
        self._process_terminator = process_terminator

        self._non_whitelist_pid: int | None = None
        self._non_whitelist_since: datetime | None = None
        self._non_whitelist_kill_attempted: bool = False

        self._state = AlertStateMachine(
            AlertPolicy(
                distract_alarm_after_s=self._config.distract_alarm_after_s,
                release_alarm_after_work_s=self._config.release_alarm_after_work_s,
            )
        )

    def tick(self, frame_bgr=None, now: datetime | None = None) -> StateUpdate:
        now = now or _now_local()

        active_window = None
        reasons: list[str] = []

        try:
            active_window = self._active_window_provider.get_foreground_app()
        except Exception:
            active_window = None

        allowed_process_set = {p.strip().lower() for p in self._config.allowed_process_names if p.strip()}
        process_name = (active_window.process_name or "").strip().lower() if active_window is not None else ""
        window_title = (active_window.window_title or "").strip() if active_window is not None else ""

        process_in_whitelist = True
        if allowed_process_set:
            process_in_whitelist = process_name in allowed_process_set

        title_ok = True
        if self._config.allowed_title_keywords:
            title_ok = any(k in window_title for k in self._config.allowed_title_keywords if k)

        allowed = is_window_allowed(
            active_window,
            allowed_process_names=self._config.allowed_process_names,
            allowed_title_keywords=self._config.allowed_title_keywords,
        )
        if not allowed:
            reasons.append('active_window_not_allowed')
            if allowed_process_set and not process_in_whitelist:
                reasons.append('active_window_process_not_allowed')
            if self._config.allowed_title_keywords and not title_ok:
                reasons.append('active_window_title_not_allowed')

        # If the foreground *process* is outside the process whitelist continuously beyond the
        # distract threshold, attempt to terminate it once.
        should_kill_process = (not allowed) and bool(allowed_process_set) and (not process_in_whitelist)
        pid = active_window.pid if active_window is not None else None
        if should_kill_process and pid is not None and pid > 0 and pid != os.getpid() and process_name:
            if self._non_whitelist_pid != pid:
                self._non_whitelist_pid = pid
                self._non_whitelist_since = now
                self._non_whitelist_kill_attempted = False

            if self._non_whitelist_since is None:
                self._non_whitelist_since = now

            elapsed_s = (now - self._non_whitelist_since).total_seconds()
            if (not self._non_whitelist_kill_attempted) and elapsed_s >= self._config.distract_alarm_after_s:
                self._non_whitelist_kill_attempted = True
                reasons.append('non_whitelist_process_termination_attempted')

                ok = False
                if self._process_terminator is not None:
                    ok = self._process_terminator.terminate_pid(pid)
                reasons.append(
                    'non_whitelist_process_terminated' if ok else 'non_whitelist_process_termination_failed'
                )
        else:
            self._non_whitelist_pid = None
            self._non_whitelist_since = None
            self._non_whitelist_kill_attempted = False

        # Vision is best-effort:
        # - If camera is disabled, ignore vision completely.
        # - If face pose is disabled/unavailable, do not force REST due to face_present=False.
        # - If frame/analyzer is missing, continue with window-only signals.
        signals = VisionSignals()

        if self._config.enable_camera:
            if not self._config.enable_face_pose:
                signals.face_present = True
            elif frame_bgr is None or self._vision_analyzer is None:
                signals.face_present = True
                if frame_bgr is None:
                    reasons.append('camera_no_frame')

        if frame_bgr is not None and self._vision_analyzer is not None:
            try:
                signals = self._vision_analyzer.analyze(frame_bgr)
            except Exception:
                signals = VisionSignals(face_present=True)
                reasons.append('vision_error')

        if self._config.enable_camera:
            if self._config.enable_yolo_phone and signals.phone_present:
                reasons.append('phone_detected')
            if self._config.enable_face_pose and signals.looking_down:
                reasons.append('looking_down')

        if self._config.enable_camera and self._config.enable_face_pose and not signals.face_present:
            observed = FocusState.REST
            reasons.append('no_face')
        else:
            observed = FocusState.DISTRACTED if reasons else FocusState.WORK

        update = self._state.update(
            Observation(
                observed_state=observed,
                reasons=tuple(reasons),
                active_window=active_window,
            ),
            now=now,
        )
        self._on_update(update)
        return update
