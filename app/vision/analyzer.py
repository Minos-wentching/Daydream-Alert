from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class VisionSignals:
    face_present: bool
    looking_down: bool
    phone_present: bool


class VisionAnalyzer:
    def __init__(self, enable_face_pose: bool = True, enable_yolo_phone: bool = True):
        self._enable_face_pose = enable_face_pose
        self._enable_yolo_phone = enable_yolo_phone

        self._face_mesh = None
        self._yolo = None
        self._yolo_device = 'cpu'

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
                from ultralytics import YOLO  # type: ignore

                self._yolo = YOLO('yolov8n.pt')
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
                    # Heuristic: nose tip lower than eye line => likely looking down.
                    left_eye = landmarks[33]
                    right_eye = landmarks[263]
                    nose_tip = landmarks[1]
                    eye_y = (left_eye.y + right_eye.y) / 2.0
                    if (nose_tip.y - eye_y) > 0.12:
                        looking_down = True
            except Exception:
                pass

        if self._yolo is not None:
            try:
                results = self._yolo.predict(
                    source=frame_bgr,
                    imgsz=640,
                    conf=0.35,
                    verbose=False,
                    device=self._yolo_device,
                )
                if results:
                    r0 = results[0]
                    if r0.boxes is not None and len(r0.boxes) > 0:
                        names = getattr(r0, 'names', None) or {}
                        for cls_id in r0.boxes.cls.tolist():
                            if names.get(int(cls_id), '') == 'cell phone':
                                phone_present = True
                                break
            except Exception:
                pass

        return VisionSignals(face_present=face_present, looking_down=looking_down, phone_present=phone_present)
