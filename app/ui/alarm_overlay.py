from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AlarmOverlay(QWidget):
    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setStyleSheet("background: #E11D48;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("请回到任务本身")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 42px; font-weight: 800;")

        subtitle = QLabel("检测到分神时间超过阈值。保持专注一会儿就会自动解除。")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255,255,255,0.92); font-size: 16px;")

        layout.addWidget(title)
        layout.addSpacing(14)
        layout.addWidget(subtitle)

    def show_overlay(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_overlay(self) -> None:
        self.hide()

