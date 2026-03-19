from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


def _make_flag_path(size: int) -> QPainterPath:
    # Simple white flag icon.
    s = float(size)
    path = QPainterPath()
    pole_x = 0.38 * s
    top = 0.12 * s
    bottom = 0.88 * s

    # Pole
    path.moveTo(pole_x, top)
    path.lineTo(pole_x, bottom)

    # Flag cloth
    x0 = pole_x
    y0 = 0.18 * s
    w = 0.46 * s
    h = 0.26 * s
    path.moveTo(x0, y0)
    path.cubicTo(x0 + 0.25 * w, y0 + 0.05 * h, x0 + 0.55 * w, y0 - 0.08 * h, x0 + w, y0 + 0.18 * h)
    path.cubicTo(x0 + 0.70 * w, y0 + 0.40 * h, x0 + 0.40 * w, y0 + 0.33 * h, x0, y0 + h)
    path.closeSubpath()

    # A couple of folds
    fold = QPainterPath()
    fold.moveTo(x0 + 0.18 * w, y0 + 0.08 * h)
    fold.cubicTo(x0 + 0.40 * w, y0 + 0.12 * h, x0 + 0.58 * w, y0 + 0.02 * h, x0 + 0.80 * w, y0 + 0.16 * h)
    path.addPath(fold)

    fold2 = QPainterPath()
    fold2.moveTo(x0 + 0.10 * w, y0 + 0.65 * h)
    fold2.cubicTo(x0 + 0.34 * w, y0 + 0.56 * h, x0 + 0.56 * w, y0 + 0.72 * h, x0 + 0.78 * w, y0 + 0.60 * h)
    path.addPath(fold2)

    return path


class SurrenderOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName('SurrenderOverlay')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet('background: #000000;')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon = QLabel()
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setFixedSize(96, 96)
        self._icon.setPixmap(self._render_flag(96))

        text = QLabel('你不行啊同志，这就坚持不住了？')
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet('color: white; font-size: 48px; font-weight: 800;')

        layout.addWidget(self._icon)
        layout.addSpacing(14)
        layout.addWidget(text)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._on_finished: Optional[Callable[[], None]] = None

        self.hide()

    def _render_flag(self, size: int):
        from PySide6.QtGui import QPixmap

        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)

        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outline = QPen(Qt.GlobalColor.white)
        outline.setWidth(max(2, int(size * 0.06)))
        outline.setCapStyle(Qt.PenCapStyle.RoundCap)
        outline.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(outline)
        p.setBrush(Qt.BrushStyle.NoBrush)

        path = _make_flag_path(size)
        p.drawPath(path)

        detail = QPen(Qt.GlobalColor.white)
        detail.setWidth(max(1, int(size * 0.02)))
        detail.setStyle(Qt.PenStyle.DotLine)
        p.setPen(detail)
        p.drawLine(int(size * 0.38), int(size * 0.60), int(size * 0.38), int(size * 0.88))

        p.end()
        return px

    def show_for(self, ms: int, *, on_finished: Optional[Callable[[], None]] = None) -> None:
        self._on_finished = on_finished
        self.show()
        self.raise_()
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
