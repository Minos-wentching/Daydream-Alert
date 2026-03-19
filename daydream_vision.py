from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VisionSignals:
    face_present: bool
    looking_down: bool
    phone_present: bool


class VisionAnalyzer:
    def __init__(
        self,
        enable_face_pose: bool = True,
        enable_yolo_phone: bool = True,
        yolo_weights_path: str = 'yolov8n.pt',
    ):
        self._enable_face_pose = enable_face_pose
        self._enable_yolo_phone = enable_yolo_phone
        self._yolo_weights_path = yolo_weights_path

        self._face_mesh = None
        self._yolo = None
        self._yolo_device = 'cpu'

        # Throttle YOLO inference to keep UI responsive on CPU.
        # - DAYDREAM_YOLO_STRIDE=5 means run YOLO once every 5 calls to analyze().
        # - DAYDREAM_YOLO_HOLD_S keeps phone_present True for a short time after a detection.
        try:
            stride_raw = (os.environ.get('DAYDREAM_YOLO_STRIDE') or '5').strip()
            self._yolo_stride = max(1, int(stride_raw))
        except Exception:
            self._yolo_stride = 5

        try:
            hold_raw = (os.environ.get('DAYDREAM_YOLO_HOLD_S') or '3.0').strip()
            self._yolo_hold_s = max(0.0, float(hold_raw))
        except Exception:
            self._yolo_hold_s = 3.0

        self._yolo_tick = 0
        self._last_phone_ts = -1e9

        if self._enable_face_pose:
            try:
                import mediapipe as mp  # type: ignore

                face_mesh = mp.solutions.face_mesh
                self._face_mesh = face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
            except Exception:
                self._face_mesh = None

        if self._enable_yolo_phone:
            try:
                weights = Path(self._yolo_weights_path)
                if weights.exists():
                    from ultralytics import YOLO  # type: ignore

                    self._yolo = YOLO(str(weights))
                    self._yolo_device = self._detect_yolo_device()
            except Exception:
                self._yolo = None
                self._yolo_device = 'cpu'

    def _detect_yolo_device(self) -> str:
        override = (os.environ.get('DAYDREAM_YOLO_DEVICE') or '').strip()
        if override:
            return override
        try:
            import torch  # type: ignore

            return 'cuda' if bool(torch.cuda.is_available()) else 'cpu'
        except Exception:
            return 'cpu'

    def analyze(self, frame_bgr) -> VisionSignals:
        face_present = False
        looking_down = False
        phone_present = False

        if self._face_mesh is not None:
            try:
                import cv2  # type: ignore

                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                result = self._face_mesh.process(frame_rgb)
                if result.multi_face_landmarks:
                    face_present = True
                    landmarks = result.multi_face_landmarks[0].landmark
                    left_eye = landmarks[33]
                    right_eye = landmarks[263]
                    nose_tip = landmarks[1]
                    eye_y = (left_eye.y + right_eye.y) / 2.0
                    if (nose_tip.y - eye_y) > 0.12:
                        looking_down = True
            except Exception:
                pass

        now_s = time.monotonic()
        if self._yolo is not None:
            self._yolo_tick += 1
            run_yolo = (self._yolo_tick % self._yolo_stride) == 1
            if run_yolo:
                try:
                    results = self._yolo.predict(
                        source=frame_bgr,
                        imgsz=480,
                        conf=0.35,
                        verbose=False,
                        device=self._yolo_device,
                    )
                except Exception:
                    # Common when a machine has a GPU but the CUDA runtime / torch build is mismatched.
                    if str(self._yolo_device).lower().startswith('cuda'):
                        self._yolo_device = 'cpu'
                        try:
                            results = self._yolo.predict(
                                source=frame_bgr,
                                imgsz=480,
                                conf=0.35,
                                verbose=False,
                                device=self._yolo_device,
                            )
                        except Exception:
                            results = []
                    else:
                        results = []

                if results:
                    r0 = results[0]
                    if r0.boxes is not None and len(r0.boxes) > 0:
                        names = getattr(r0, 'names', None) or {}
                        for cls_id in r0.boxes.cls.tolist():
                            if names.get(int(cls_id), '') == 'cell phone':
                                self._last_phone_ts = now_s
                                break

            phone_present = (now_s - self._last_phone_ts) <= self._yolo_hold_s

        return VisionSignals(face_present=face_present, looking_down=looking_down, phone_present=phone_present)
