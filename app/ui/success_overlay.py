from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


def _make_rose_path(size: int) -> tuple[QPainterPath, list[QPainterPath]]:
    s = float(size)

    # Outer rose silhouette (stylized)
    outer = QPainterPath()
    outer.moveTo(0.50 * s, 0.10 * s)
    outer.cubicTo(0.72 * s, 0.10 * s, 0.88 * s, 0.26 * s, 0.86 * s, 0.46 * s)
    outer.cubicTo(0.84 * s, 0.66 * s, 0.70 * s, 0.82 * s, 0.50 * s, 0.88 * s)
    outer.cubicTo(0.30 * s, 0.82 * s, 0.16 * s, 0.66 * s, 0.14 * s, 0.46 * s)
    outer.cubicTo(0.12 * s, 0.26 * s, 0.28 * s, 0.10 * s, 0.50 * s, 0.10 * s)
    outer.closeSubpath()

    # Inner spiral / petals
    details: list[QPainterPath] = []

    spiral = QPainterPath()
    spiral.moveTo(0.52 * s, 0.30 * s)
    spiral.cubicTo(0.62 * s, 0.26 * s, 0.70 * s, 0.34 * s, 0.66 * s, 0.42 * s)
    spiral.cubicTo(0.62 * s, 0.50 * s, 0.48 * s, 0.48 * s, 0.46 * s, 0.40 * s)
    spiral.cubicTo(0.44 * s, 0.32 * s, 0.56 * s, 0.30 * s, 0.58 * s, 0.38 * s)
    spiral.cubicTo(0.60 * s, 0.46 * s, 0.50 * s, 0.54 * s, 0.40 * s, 0.52 * s)
    spiral.cubicTo(0.30 * s, 0.50 * s, 0.26 * s, 0.40 * s, 0.32 * s, 0.34 * s)
    details.append(spiral)

    petal1 = QPainterPath()
    petal1.moveTo(0.22 * s, 0.48 * s)
    petal1.cubicTo(0.30 * s, 0.36 * s, 0.40 * s, 0.30 * s, 0.50 * s, 0.32 * s)
    petal1.cubicTo(0.38 * s, 0.40 * s, 0.32 * s, 0.52 * s, 0.34 * s, 0.64 * s)
    details.append(petal1)

    petal2 = QPainterPath()
    petal2.moveTo(0.78 * s, 0.48 * s)
    petal2.cubicTo(0.70 * s, 0.36 * s, 0.60 * s, 0.30 * s, 0.50 * s, 0.32 * s)
    petal2.cubicTo(0.62 * s, 0.40 * s, 0.68 * s, 0.52 * s, 0.66 * s, 0.64 * s)
    details.append(petal2)

    vein1 = QPainterPath()
    vein1.moveTo(0.50 * s, 0.52 * s)
    vein1.cubicTo(0.46 * s, 0.58 * s, 0.44 * s, 0.66 * s, 0.46 * s, 0.74 * s)
    details.append(vein1)

    vein2 = QPainterPath()
    vein2.moveTo(0.50 * s, 0.52 * s)
    vein2.cubicTo(0.54 * s, 0.58 * s, 0.56 * s, 0.66 * s, 0.54 * s, 0.74 * s)
    details.append(vein2)

    return outer, details


class SuccessOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName('SuccessOverlay')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet('background: #000000;')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon = QLabel()
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setFixedSize(96, 96)
        self._icon.setPixmap(self._render_rose(96))

        text = QLabel('太棒了你坚持到了最后奖励一个么么哒')
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

    def _render_rose(self, size: int):
        from PySide6.QtGui import QPixmap

        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)

        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer, details = _make_rose_path(size)

        outline = QPen(Qt.GlobalColor.white)
        outline.setWidth(max(2, int(size * 0.06)))
        outline.setCapStyle(Qt.PenCapStyle.RoundCap)
        outline.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(outline)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(outer)

        inner = QPen(Qt.GlobalColor.white)
        inner.setWidth(max(1, int(size * 0.025)))
        inner.setCapStyle(Qt.PenCapStyle.RoundCap)
        inner.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(inner)
        for d in details:
            p.drawPath(d)

        # Fine texture lines
        texture = QPen(Qt.GlobalColor.white)
        texture.setWidth(max(1, int(size * 0.012)))
        texture.setStyle(Qt.PenStyle.DotLine)
        p.setPen(texture)
        for i in range(6):
            y = int(size * (0.30 + i * 0.07))
            p.drawLine(int(size * 0.28), y, int(size * 0.72), y)

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
