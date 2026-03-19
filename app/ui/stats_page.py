from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.focus_stats import load_period_stats


def _ensure_button_text_visible(btn: QPushButton, extra_px: int = 34) -> None:
    btn.setMinimumWidth(btn.fontMetrics().horizontalAdvance(btn.text()) + extra_px)


def _inline_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName('InlineLabel')
    return label


def _local_tz():
    return datetime.now().astimezone().tzinfo


def _start_of_day(d: date) -> datetime:
    return datetime.combine(d, time(0, 0, 0), tzinfo=_local_tz())


def _start_of_week(d: date) -> datetime:
    monday = d - timedelta(days=d.weekday())
    return _start_of_day(monday)


def _fmt_seconds(seconds: float) -> str:
    s = max(0, int(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f'{h}h {m}m'
    if m > 0:
        return f'{m}m {sec}s'
    return f'{sec}s'


class StatsPage(QWidget):
    back_requested = Signal()

    def __init__(self, db_path: Path | None = None):
        super().__init__()
        self.setObjectName('Root')
        self._db_path = db_path or (Path('data') / 'daydream_focus.sqlite3')

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 26)
        root.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel('专注统计')
        title.setObjectName('Title')
        subtitle = QLabel('日报 / 周报（从本地 SQLite 读取）')
        subtitle.setObjectName('SubTitle')
        header_left = QVBoxLayout()
        header_left.addWidget(title)
        header_left.addWidget(subtitle)
        header.addLayout(header_left)
        header.addStretch(1)

        self.back_btn = QPushButton('返回首页')
        self.back_btn.setObjectName('Ghost')
        _ensure_button_text_visible(self.back_btn)
        self.back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(self.back_btn)
        root.addLayout(header)

        card = QFrame()
        card.setObjectName('Card')
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setHorizontalSpacing(16)
        card_layout.setVerticalSpacing(10)

        self.mode = QComboBox()
        self.mode.setObjectName('KeepLight')
        self.mode.addItems(['日报', '周报'])
        self.mode.currentIndexChanged.connect(self.refresh)

        self.pick_date = QDateEdit(QDate.currentDate())
        self.pick_date.setCalendarPopup(True)
        self.pick_date.dateChanged.connect(self.refresh)

        self.refresh_btn = QPushButton('刷新')
        _ensure_button_text_visible(self.refresh_btn)
        self.refresh_btn.clicked.connect(self.refresh)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(10)
        ctrl.addWidget(_inline_label('视图'))
        ctrl.addWidget(self.mode)
        ctrl.addSpacing(10)
        ctrl.addWidget(_inline_label('日期'))
        ctrl.addWidget(self.pick_date)
        ctrl.addStretch(1)
        ctrl.addWidget(self.refresh_btn)
        ctrl_container = QWidget()
        ctrl_container.setLayout(ctrl)
        card_layout.addWidget(ctrl_container, 0, 0, 1, 2)

        self.summary = QLabel('—')
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.summary.setStyleSheet('font-size: 16px; font-weight: 700;')
        card_layout.addWidget(self.summary, 1, 0, 1, 2)

        self.sessions_table = QTableWidget(0, 6)
        self.sessions_table.setHorizontalHeaderLabels(['开始', '结束', '任务', '工作', '分神', '休息'])
        self.sessions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sessions_table.setAlternatingRowColors(True)
        self.sessions_table.horizontalHeader().setStretchLastSection(True)
        card_layout.addWidget(self.sessions_table, 2, 0, 1, 2)

        self.top_processes = QTableWidget(0, 2)
        self.top_processes.setHorizontalHeaderLabels(['最易分神进程', '分神时长'])
        self.top_processes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.top_processes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.top_processes.setAlternatingRowColors(True)
        self.top_processes.horizontalHeader().setStretchLastSection(True)
        card_layout.addWidget(self.top_processes, 3, 0, 1, 2)

        root.addWidget(card)
        root.addStretch(1)

        self.refresh()

    def _current_period(self) -> tuple[datetime, datetime]:
        d = self.pick_date.date().toPython()
        if self.mode.currentText() == '周报':
            start = _start_of_week(d)
            end = start + timedelta(days=7)
            return start, end
        start = _start_of_day(d)
        end = start + timedelta(days=1)
        return start, end

    def refresh(self) -> None:
        start_at, end_at = self._current_period()
        try:
            stats = load_period_stats(self._db_path, start_at=start_at, end_at=end_at)
        except Exception as exc:
            QMessageBox.warning(self, '统计读取失败', f'读取 SQLite 失败：{exc}')
            return

        period_name = '周报' if self.mode.currentText() == '周报' else '日报'
        self.summary.setText(
            f"{period_name} | {start_at.strftime('%Y-%m-%d')} → {end_at.strftime('%Y-%m-%d')}  "
            f'| 会话 {len(stats.sessions)}  '
            f'| 工作 {_fmt_seconds(stats.work_s)}  '
            f'| 分神 {_fmt_seconds(stats.distracted_s)}  '
            f'| 休息 {_fmt_seconds(stats.rest_s)}'
        )

        self.sessions_table.setRowCount(0)
        for s in stats.sessions:
            row = self.sessions_table.rowCount()
            self.sessions_table.insertRow(row)
            self.sessions_table.setItem(row, 0, QTableWidgetItem(s.started_at.strftime('%m-%d %H:%M')))
            self.sessions_table.setItem(row, 1, QTableWidgetItem(s.ended_at.strftime('%m-%d %H:%M')))
            self.sessions_table.setItem(row, 2, QTableWidgetItem(s.task_name))
            self.sessions_table.setItem(row, 3, QTableWidgetItem(_fmt_seconds(s.work_s)))
            self.sessions_table.setItem(row, 4, QTableWidgetItem(_fmt_seconds(s.distracted_s)))
            self.sessions_table.setItem(row, 5, QTableWidgetItem(_fmt_seconds(s.rest_s)))

        self.top_processes.setRowCount(0)
        for name, dur_s in stats.top_distracted_processes:
            row = self.top_processes.rowCount()
            self.top_processes.insertRow(row)
            self.top_processes.setItem(row, 0, QTableWidgetItem(name))
            self.top_processes.setItem(row, 1, QTableWidgetItem(_fmt_seconds(dur_s)))
