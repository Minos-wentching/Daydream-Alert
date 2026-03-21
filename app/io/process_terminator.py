from __future__ import annotations

from typing import Protocol


class ProcessTerminator(Protocol):
    def terminate_pid(self, pid: int) -> bool:
        """Attempt to terminate a process by PID.

        Returns True if a termination/kill signal was successfully issued.
        """


class WindowsProcessTerminator:
    def __init__(self, graceful_timeout_s: float = 2.0):
        try:
            import psutil  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError('WindowsProcessTerminator requires psutil') from exc

        self._psutil = psutil
        self._graceful_timeout_s = graceful_timeout_s

    def terminate_pid(self, pid: int) -> bool:
        try:
            proc = self._psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=self._graceful_timeout_s)
            except self._psutil.TimeoutExpired:
                proc.kill()
            return True
        except Exception:
            return False
