from __future__ import annotations

from app.core.models import ActiveWindowInfo


class ActiveWindowProvider:
    def get_foreground_app(self) -> ActiveWindowInfo | None:
        raise NotImplementedError


class WindowsActiveWindowProvider(ActiveWindowProvider):
    def __init__(self):
        try:
            import win32gui  # type: ignore
            import win32process  # type: ignore
            import psutil  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("WindowsActiveWindowProvider requires pywin32 + psutil") from exc

        self._win32gui = win32gui
        self._win32process = win32process
        self._psutil = psutil

    def get_foreground_app(self) -> ActiveWindowInfo | None:
        hwnd = self._win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        title = self._win32gui.GetWindowText(hwnd) or ""
        _, pid = self._win32process.GetWindowThreadProcessId(hwnd)

        process_name = ""
        try:
            process_name = self._psutil.Process(pid).name()
        except Exception:
            process_name = ""

        return ActiveWindowInfo(process_name=process_name, window_title=title, pid=pid)

