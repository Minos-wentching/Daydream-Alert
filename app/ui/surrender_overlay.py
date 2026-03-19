from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SurrenderOverlay(QWidget):
    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setStyleSheet('background: #000000;')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        flag = QLabel('🏳')
        flag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flag.setStyleSheet('color: white; font-size: 96px;')

        text = QLabel('你不行啊同志，这就坚持不住了？')
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet('color: white; font-size: 48px; font-weight: 800;')

        layout.addWidget(flag)
        layout.addSpacing(14)
        layout.addWidget(text)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._on_finished: Optional[Callable[[], None]] = None

    def show_for(self, ms: int, *, on_finished: Optional[Callable[[], None]] = None) -> None:
        self._on_finished = on_finished
        self.show()
        self.raise_()
        self.activateWindow()
        self._timer.start(int(ms))

    def hide_overlay(self) -> None:
        try:
            self._timer.stop()
        except Exception:
            pass
        self.hide()

    def _on_timeout(self) -> None:
        self.hide()
        cb = self._on_finished
        self._on_finished = None
        if cb is not None:
            cb()
