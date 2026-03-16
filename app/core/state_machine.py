from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.core.models import FocusState, Observation, StateUpdate


@dataclass
class AlertPolicy:
    distract_alarm_after_s: int = 3 * 60
    release_alarm_after_work_s: int = 2 * 60


class AlertStateMachine:
    def __init__(self, policy: AlertPolicy):
        self._policy = policy
        self._last_ts: Optional[datetime] = None
        self._alarm_on: bool = False
        self._distracted_accumulated_s: float = 0.0
        self._work_streak_s: float = 0.0

    @property
    def alarm_on(self) -> bool:
        return self._alarm_on

    @property
    def distracted_accumulated_s(self) -> float:
        return self._distracted_accumulated_s

    @property
    def work_streak_s(self) -> float:
        return self._work_streak_s

    def update(self, observation: Observation, now: datetime) -> StateUpdate:
        if self._last_ts is None:
            self._last_ts = now
            return StateUpdate(
                now=now,
                observed_state=observation.observed_state,
                alarm_on=self._alarm_on,
                distracted_accumulated_s=self._distracted_accumulated_s,
                work_streak_s=self._work_streak_s,
                reasons=observation.reasons,
                active_window=observation.active_window,
            )

        dt = (now - self._last_ts).total_seconds()
        if dt < 0:
            dt = 0
        self._last_ts = now

        if observation.observed_state == FocusState.DISTRACTED:
            self._distracted_accumulated_s += dt
            self._work_streak_s = 0.0
        elif observation.observed_state == FocusState.WORK:
            self._work_streak_s += dt
        else:  # REST
            self._work_streak_s = 0.0

        if not self._alarm_on and self._distracted_accumulated_s >= self._policy.distract_alarm_after_s:
            self._alarm_on = True

        if self._alarm_on and self._work_streak_s >= self._policy.release_alarm_after_work_s:
            self._alarm_on = False

        return StateUpdate(
            now=now,
            observed_state=observation.observed_state,
            alarm_on=self._alarm_on,
            distracted_accumulated_s=self._distracted_accumulated_s,
            work_streak_s=self._work_streak_s,
            reasons=observation.reasons,
            active_window=observation.active_window,
        )

