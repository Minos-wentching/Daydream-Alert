from datetime import datetime, timedelta, timezone

from app.core.models import FocusState, Observation
from app.core.state_machine import AlertPolicy, AlertStateMachine


def _ts(seconds: int) -> datetime:
    return datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=seconds)


def test_alarm_triggers_after_distracted_threshold():
    sm = AlertStateMachine(AlertPolicy(distract_alarm_after_s=180, release_alarm_after_work_s=120))
    sm.update(Observation(FocusState.DISTRACTED), _ts(0))
    u = sm.update(Observation(FocusState.DISTRACTED), _ts(180))
    assert u.alarm_on is True


def test_alarm_releases_after_work_streak():
    sm = AlertStateMachine(AlertPolicy(distract_alarm_after_s=10, release_alarm_after_work_s=120))
    sm.update(Observation(FocusState.DISTRACTED), _ts(0))
    sm.update(Observation(FocusState.DISTRACTED), _ts(10))
    assert sm.alarm_on is True
    sm.update(Observation(FocusState.WORK), _ts(11))
    u = sm.update(Observation(FocusState.WORK), _ts(131))
    assert u.alarm_on is False


def test_rest_does_not_release_alarm():
    sm = AlertStateMachine(AlertPolicy(distract_alarm_after_s=10, release_alarm_after_work_s=120))
    sm.update(Observation(FocusState.DISTRACTED), _ts(0))
    sm.update(Observation(FocusState.DISTRACTED), _ts(10))
    assert sm.alarm_on is True
    sm.update(Observation(FocusState.REST), _ts(11))
    u = sm.update(Observation(FocusState.REST), _ts(1000))
    assert u.alarm_on is True

