from datetime import datetime, timedelta, timezone

from app.core.models import ActiveWindowInfo, TaskConfig
from app.core.monitor_controller import MonitorController


class _Provider:
    def __init__(self):
        self.active_window = None

    def get_foreground_app(self):
        return self.active_window


class _Terminator:
    def __init__(self, ok: bool = True):
        self.ok = ok
        self.calls: list[int] = []

    def terminate_pid(self, pid: int) -> bool:
        self.calls.append(pid)
        return self.ok


def _ts(seconds: int) -> datetime:
    return datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=seconds)


def _config(*, threshold_s: int, allowed_process_names: list[str], allowed_title_keywords: list[str] | None = None):
    allowed_title_keywords = allowed_title_keywords or []
    return TaskConfig(
        task_name='t',
        start_at=_ts(0),
        end_at=_ts(3600),
        distract_alarm_after_s=threshold_s,
        release_alarm_after_work_s=120,
        allowed_process_names=allowed_process_names,
        allowed_title_keywords=allowed_title_keywords,
        enable_camera=False,
        enable_yolo_phone=False,
        enable_face_pose=False,
    )


def test_kills_foreground_process_after_non_whitelist_threshold():
    provider = _Provider()
    terminator = _Terminator(ok=True)

    cfg = _config(threshold_s=10, allowed_process_names=['good.exe'])
    mc = MonitorController(
        config=cfg,
        active_window_provider=provider,
        vision_analyzer=None,
        on_update=lambda _u: None,
        process_terminator=terminator,
    )

    provider.active_window = ActiveWindowInfo(process_name='bad.exe', window_title='Bad', pid=111)
    mc.tick(now=_ts(0))
    u = mc.tick(now=_ts(10))

    assert u.alarm_on is True
    assert terminator.calls == [111]
    assert 'non_whitelist_process_termination_attempted' in u.reasons


def test_non_whitelist_timer_resets_when_window_becomes_allowed():
    provider = _Provider()
    terminator = _Terminator(ok=True)

    cfg = _config(threshold_s=10, allowed_process_names=['good.exe'])
    mc = MonitorController(
        config=cfg,
        active_window_provider=provider,
        vision_analyzer=None,
        on_update=lambda _u: None,
        process_terminator=terminator,
    )

    provider.active_window = ActiveWindowInfo(process_name='bad.exe', window_title='Bad', pid=111)
    mc.tick(now=_ts(0))

    provider.active_window = ActiveWindowInfo(process_name='good.exe', window_title='Good', pid=222)
    mc.tick(now=_ts(5))

    provider.active_window = ActiveWindowInfo(process_name='bad.exe', window_title='Bad', pid=111)
    mc.tick(now=_ts(6))
    mc.tick(now=_ts(15))

    assert terminator.calls == []


def test_title_mismatch_does_not_kill_process_in_process_whitelist():
    provider = _Provider()
    terminator = _Terminator(ok=True)

    cfg = _config(
        threshold_s=10,
        allowed_process_names=['chrome.exe'],
        allowed_title_keywords=['Notion'],
    )
    mc = MonitorController(
        config=cfg,
        active_window_provider=provider,
        vision_analyzer=None,
        on_update=lambda _u: None,
        process_terminator=terminator,
    )

    provider.active_window = ActiveWindowInfo(process_name='chrome.exe', window_title='YouTube', pid=333)
    mc.tick(now=_ts(0))
    u = mc.tick(now=_ts(10))

    assert u.alarm_on is True
    assert terminator.calls == []
