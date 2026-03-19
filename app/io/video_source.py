from __future__ import annotations

from typing import Optional


class VideoSource:
    def open(self) -> None:
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class LocalWebcamSource(VideoSource):
    def __init__(self, camera_index: int = 0, backend: Optional[int] = None):
        try:
            import cv2  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError('LocalWebcamSource requires opencv-python') from exc

        self._cv2 = cv2
        self._camera_index = camera_index
        self._backend = backend
        self._cap = None

    def open(self) -> None:
        backends: list[int] = []
        if self._backend is not None:
            backends = [int(self._backend)]
        else:
            for name in ('CAP_DSHOW', 'CAP_MSMF', 'CAP_ANY'):
                if hasattr(self._cv2, name):
                    backends.append(int(getattr(self._cv2, name)))

        last_error = None
        for backend in backends or [0]:
            cap = self._cv2.VideoCapture(self._camera_index, backend)
            try:
                if cap is not None and cap.isOpened():
                    self._cap = cap
                    cap.read()
                    return
            except Exception as exc:
                last_error = str(exc)
            try:
                if cap is not None:
                    cap.release()
            except Exception:
                pass

        detail = f' ({last_error})' if last_error else ''
        raise RuntimeError(f'Failed to open webcam{detail}')

    def read(self):
        if self._cap is None:
            return None
        ok, frame = self._cap.read()
        if not ok:
            return None
        return frame

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


def probe_local_webcam(camera_index: int = 0) -> tuple[bool, str | None]:
    '''Try open+read one frame; used for permission/availability checks.'''

    src = None
    try:
        src = LocalWebcamSource(camera_index)
        src.open()
        frame = src.read()
        if frame is None:
            return False, 'Opened but got empty frames'
        return True, None
    except Exception as exc:
        return False, str(exc)
    finally:
        try:
            if src is not None:
                src.close()
        except Exception:
            pass


class RtspStreamSource(VideoSource):
    def __init__(self, url: str):
        self._url = url

    def open(self) -> None:  # pragma: no cover
        raise NotImplementedError('RTSP source is reserved for future extension.')

    def read(self):  # pragma: no cover
        return None

    def close(self) -> None:  # pragma: no cover
        return None
