from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.models import FocusState, StateUpdate, TaskConfig


def _ensure_button_text_visible(btn: QPushButton, extra_px: int = 34) -> None:
    btn.setMinimumWidth(btn.fontMetrics().horizontalAdvance(btn.text()) + extra_px)


class SessionPage(QWidget):
    exit_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName('Root')

        self._config: TaskConfig | None = None
        self._started_at: datetime | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 26)
        root.setSpacing(14)

        header = QHBoxLayout()
        self.title = QLabel('任务进行中')
        self.title.setObjectName('Title')
        self.subtitle = QLabel('')
        self.subtitle.setObjectName('SubTitle')
        header_left = QVBoxLayout()
        header_left.addWidget(self.title)
        header_left.addWidget(self.subtitle)
        header.addLayout(header_left)
        header.addStretch(1)
        root.addLayout(header)

        card = QFrame()
        card.setObjectName('Card')
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setHorizontalSpacing(16)
        card_layout.setVerticalSpacing(10)

        self.state_label = QLabel('状态：-')
        self.state_label.setStyleSheet('font-size: 18px; font-weight: 700;')
        self.distracted_label = QLabel('累计分神：0s')
        self.work_streak_label = QLabel('持续工作：0s')
        self.window_label = QLabel('前台窗口：-')
        self.reasons_label = QLabel('原因：-')

        left = QVBoxLayout()
        left.addWidget(self.state_label)
        left.addWidget(self.distracted_label)
        left.addWidget(self.work_streak_label)
        left.addSpacing(10)
        left.addWidget(self.window_label)
        left.addWidget(self.reasons_label)
        left.addStretch(1)
        left_container = QWidget()
        left_container.setLayout(left)

        self.preview = QLabel()
        self.preview.setObjectName('PreviewBox')
        self.preview.setFixedSize(460, 300)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setText('摄像头预览')

        card_layout.addWidget(left_container, 0, 0, 1, 1)
        card_layout.addWidget(self.preview, 0, 1, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)

        root.addWidget(card)

        footer = QHBoxLayout()
        self.exit_btn = QPushButton('退出')
        self.exit_btn.setObjectName('Ghost')
        _ensure_button_text_visible(self.exit_btn)
        self.exit_btn.clicked.connect(self.exit_requested.emit)
        footer.addWidget(self.exit_btn)
        footer.addStretch(1)
        root.addLayout(footer)

    def set_config(self, config: TaskConfig) -> None:
        self._config = config
        self.title.setText(f'任务：{config.task_name}')
        self.subtitle.setText(
            f"{config.start_at.strftime('%Y-%m-%d %H:%M')} → {config.end_at.strftime('%Y-%m-%d %H:%M')}"
        )
        self._started_at = None

    def mark_started(self, started_at: datetime) -> None:
        self._started_at = started_at

    def set_preview_frame(self, frame_bgr) -> None:
        try:
            import cv2  # type: ignore
        except Exception:
            return

        h, w, _ = frame_bgr.shape
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        bytes_per_line = int(rgb.strides[0])
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg).scaled(
            self.preview.width(),
            self.preview.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview.setPixmap(pix)

    def on_state_update(self, update: StateUpdate) -> None:
        state_text = {
            FocusState.WORK: '工作',
            FocusState.DISTRACTED: '分神',
            FocusState.REST: '休息',
        }.get(update.observed_state, '-')
        alarm_text = '（警报中）' if update.alarm_on else ''
        self.state_label.setText(f'状态：{state_text}{alarm_text}')
        self.distracted_label.setText(f'累计分神：{int(update.distracted_accumulated_s)}s')
        self.work_streak_label.setText(f'持续工作：{int(update.work_streak_s)}s')

        if update.active_window is not None:
            self.window_label.setText(
                f'前台窗口：{update.active_window.process_name} | {update.active_window.window_title}'
            )
        else:
            self.window_label.setText('前台窗口：-')

        self.reasons_label.setText('原因：' + (', '.join(update.reasons) if update.reasons else '-'))
