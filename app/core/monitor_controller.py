from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from app.core.models import FocusState, Observation, StateUpdate, TaskConfig
from app.core.state_machine import AlertPolicy, AlertStateMachine
from app.core.whitelist import is_window_allowed


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
    ):
        self._config = config.normalized()
        self._active_window_provider = active_window_provider
        self._vision_analyzer = vision_analyzer
        self._on_update = on_update

        self._state = AlertStateMachine(
            AlertPolicy(
                distract_alarm_after_s=self._config.distract_alarm_after_s,
                release_alarm_after_work_s=self._config.release_alarm_after_work_s,
            )
        )

    def tick(self, frame_bgr=None) -> StateUpdate:
        now = _now_local()

        active_window = None
        reasons: list[str] = []

        try:
            active_window = self._active_window_provider.get_foreground_app()
        except Exception:
            active_window = None

        allowed = is_window_allowed(
            active_window,
            allowed_process_names=self._config.allowed_process_names,
            allowed_title_keywords=self._config.allowed_title_keywords,
        )
        if not allowed:
            reasons.append("active_window_not_allowed")

        signals = VisionSignals()
        if frame_bgr is not None and self._vision_analyzer is not None:
            try:
                signals = self._vision_analyzer.analyze(frame_bgr)
            except Exception:
                signals = VisionSignals()

        if self._config.enable_camera:
            if self._config.enable_yolo_phone and signals.phone_present:
                reasons.append("phone_detected")
            if self._config.enable_face_pose and signals.looking_down:
                reasons.append("looking_down")

        if self._config.enable_camera and not signals.face_present:
            observed = FocusState.REST
            reasons.append("no_face")
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

