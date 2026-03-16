from __future__ import annotations


class VideoSource:
    def open(self) -> None:
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class LocalWebcamSource(VideoSource):
    def __init__(self, camera_index: int = 0):
        try:
            import cv2  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("LocalWebcamSource requires opencv-python") from exc

        self._cv2 = cv2
        self._camera_index = camera_index
        self._cap = None

    def open(self) -> None:
        self._cap = self._cv2.VideoCapture(self._camera_index, self._cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            raise RuntimeError("Failed to open webcam")

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


class RtspStreamSource(VideoSource):
    def __init__(self, url: str):
        self._url = url

    def open(self) -> None:  # pragma: no cover
        raise NotImplementedError("RTSP source is reserved for future extension.")

    def read(self):  # pragma: no cover
        return None

    def close(self) -> None:  # pragma: no cover
        return None

