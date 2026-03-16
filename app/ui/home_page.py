from __future__ import annotations

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.models import TaskConfig, normalize_lines


class HomePage(QWidget):
    start_requested = Signal(TaskConfig)

    def __init__(self):
        super().__init__()
        self.setObjectName("Root")

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 26)
        root.setSpacing(14)

        title = QLabel("Daydream Focus")
        title.setObjectName("Title")
        subtitle = QLabel("本地专注检测：摄像头 + 当前前台窗口（仅记录时间段，不保存画面）")
        subtitle.setObjectName("SubTitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: rgba(255,255,255,0.45); border: 1px solid rgba(16,42,67,0.10); border-radius: 16px; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(10)

        self.task_name = QLineEdit()
        self.task_name.setPlaceholderText("例如：数学作业 / 论文写作 / 刷题")
        form.addRow("任务名称", self.task_name)

        self.start_at = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_at.setCalendarPopup(True)
        self.end_at = QDateTimeEdit(QDateTime.currentDateTime().addSecs(60 * 60))
        self.end_at.setCalendarPopup(True)

        time_row = QHBoxLayout()
        time_row.addWidget(self.start_at)
        time_row.addWidget(QLabel("→"))
        time_row.addWidget(self.end_at)
        time_container = QWidget()
        time_container.setLayout(time_row)
        form.addRow("起止时间", time_container)

        self.distract_after = QSpinBox()
        self.distract_after.setRange(30, 60 * 60)
        self.distract_after.setValue(3 * 60)
        self.distract_after.setSuffix(" 秒（分神累计触发警报）")
        form.addRow("触发阈值", self.distract_after)

        self.release_after = QSpinBox()
        self.release_after.setRange(10, 60 * 60)
        self.release_after.setValue(2 * 60)
        self.release_after.setSuffix(" 秒（持续工作解除警报）")
        form.addRow("解除阈值", self.release_after)

        self.process_whitelist = QTextEdit()
        self.process_whitelist.setPlaceholderText(
            "允许的进程名（每行一个或用逗号分隔）\n例如：WINWORD.EXE\nchrome.exe\ncode.exe"
        )
        self.process_whitelist.setFixedHeight(88)
        form.addRow("进程白名单", self.process_whitelist)

        self.title_keywords = QTextEdit()
        self.title_keywords.setPlaceholderText("允许的窗口标题关键词（可选）\n例如：作业 / LeetCode / 论文 / Notion")
        self.title_keywords.setFixedHeight(70)
        form.addRow("标题关键词", self.title_keywords)

        self.enable_camera = QCheckBox("启用摄像头检测（建议开启）")
        self.enable_camera.setChecked(True)
        self.enable_yolo = QCheckBox("启用手机检测（YOLOv8，CPU 上可能偏重）")
        self.enable_yolo.setChecked(True)
        self.enable_face = QCheckBox("启用低头/视线粗判（MediaPipe）")
        self.enable_face.setChecked(True)

        form.addRow("检测开关", self.enable_camera)
        form.addRow("", self.enable_face)
        form.addRow("", self.enable_yolo)

        card_layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.start_btn = QPushButton("开始任务")
        buttons.addWidget(self.start_btn)
        card_layout.addLayout(buttons)

        root.addWidget(card)
        root.addStretch(1)

        self.start_btn.clicked.connect(self._on_start)

    def _on_start(self) -> None:
        name = self.task_name.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请先填写任务名称。")
            return

        start_at = self.start_at.dateTime().toPython()
        end_at = self.end_at.dateTime().toPython()
        if end_at <= start_at:
            QMessageBox.warning(self, "提示", "结束时间需要晚于开始时间。")
            return

        config = TaskConfig(
            task_name=name,
            start_at=start_at,
            end_at=end_at,
            distract_alarm_after_s=int(self.distract_after.value()),
            release_alarm_after_work_s=int(self.release_after.value()),
            allowed_process_names=normalize_lines([self.process_whitelist.toPlainText()]),
            allowed_title_keywords=normalize_lines([self.title_keywords.toPlainText()]),
            enable_camera=bool(self.enable_camera.isChecked()),
            enable_yolo_phone=bool(self.enable_yolo.isChecked()),
            enable_face_pose=bool(self.enable_face.isChecked()),
        ).normalized()

        self.start_requested.emit(config)

