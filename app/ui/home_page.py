from __future__ import annotations

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
from app.core.whitelist_templates import WhitelistTemplateStore


def _form_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName('FormLabel')
    return label


def _ensure_button_text_visible(btn: QPushButton, extra_px: int = 34) -> None:
    btn.setMinimumWidth(btn.fontMetrics().horizontalAdvance(btn.text()) + extra_px)


class HomePage(QWidget):
    start_requested = Signal(TaskConfig)
    stats_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName('Root')

        self._templates = WhitelistTemplateStore()

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 26)
        root.setSpacing(14)

        title = QLabel('Daydream Focus')
        title.setObjectName('Title')
        subtitle = QLabel('本地专注检测：摄像头 + 当前前台窗口（仅记录时间段，不保存画面）')
        subtitle.setObjectName('SubTitle')
        root.addWidget(title)
        root.addWidget(subtitle)

        card = QFrame()
        card.setObjectName('Card')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(10)

        self.task_name = QLineEdit()
        self.task_name.setPlaceholderText('例如：数学作业 / 论文写作 / 刷题')
        form.addRow(_form_label('任务名称'), self.task_name)

        self.start_at = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_at.setCalendarPopup(True)
        self.end_at = QDateTimeEdit(QDateTime.currentDateTime().addSecs(60 * 60))
        self.end_at.setCalendarPopup(True)

        time_row = QHBoxLayout()
        time_row.setSpacing(10)
        time_row.addWidget(self.start_at)
        arrow = QLabel('→')
        arrow.setObjectName('InlineLabel')
        time_row.addWidget(arrow)
        time_row.addWidget(self.end_at)
        time_container = QWidget()
        time_container.setLayout(time_row)
        form.addRow(_form_label('起止时间'), time_container)

        self.distract_after = QSpinBox()
        self.distract_after.setRange(30, 60 * 60)
        self.distract_after.setValue(3 * 60)
        self.distract_after.setSuffix(' 秒（分神累计触发警报）')
        form.addRow(_form_label('触发阈值'), self.distract_after)

        self.release_after = QSpinBox()
        self.release_after.setRange(10, 60 * 60)
        self.release_after.setValue(2 * 60)
        self.release_after.setSuffix(' 秒（持续工作解除警报）')
        form.addRow(_form_label('解除阈值'), self.release_after)

        self.process_whitelist = QTextEdit()
        self.process_whitelist.setPlaceholderText(
            '允许的进程名（每行一个或用逗号分隔）\n例如：WINWORD.EXE\nchrome.exe\ncode.exe'
        )
        self.process_whitelist.setFixedHeight(88)
        form.addRow(_form_label('进程白名单'), self.process_whitelist)

        self.title_keywords = QTextEdit()
        self.title_keywords.setPlaceholderText('允许的窗口标题关键词（可选）\n例如：作业 / LeetCode / 论文 / Notion')
        self.title_keywords.setFixedHeight(70)
        form.addRow(_form_label('标题关键词'), self.title_keywords)

        self.template_select = QComboBox()
        self.apply_template_btn = QPushButton('一键套用')
        self.apply_template_btn.setObjectName('Ghost')
        _ensure_button_text_visible(self.apply_template_btn)
        self.apply_template_btn.clicked.connect(self._on_apply_template)

        tpl_row = QHBoxLayout()
        tpl_row.setSpacing(10)
        tpl_row.addWidget(self.template_select, 1)
        tpl_row.addWidget(self.apply_template_btn)
        tpl_container = QWidget()
        tpl_container.setLayout(tpl_row)
        form.addRow(_form_label('白名单模板'), tpl_container)

        self.template_name = QLineEdit()
        self.template_name.setPlaceholderText('保存当前白名单为模板：例如 写作 / 刷题 / 英语')
        self.save_template_btn = QPushButton('保存模板')
        self.save_template_btn.setObjectName('Ghost')
        _ensure_button_text_visible(self.save_template_btn)
        self.save_template_btn.clicked.connect(self._on_save_template)
        self.delete_template_btn = QPushButton('删除模板')
        self.delete_template_btn.setObjectName('Ghost')
        _ensure_button_text_visible(self.delete_template_btn)
        self.delete_template_btn.clicked.connect(self._on_delete_template)

        tpl_manage = QHBoxLayout()
        tpl_manage.setSpacing(10)
        tpl_manage.addWidget(self.template_name, 1)
        tpl_manage.addWidget(self.save_template_btn)
        tpl_manage.addWidget(self.delete_template_btn)
        tpl_manage_container = QWidget()
        tpl_manage_container.setLayout(tpl_manage)
        form.addRow(QLabel(''), tpl_manage_container)

        self.enable_camera = QCheckBox('启用摄像头检测（建议开启）')
        self.enable_camera.setChecked(True)
        self.enable_yolo = QCheckBox('启用手机检测（YOLOv8，CPU 上可能偏重）')
        self.enable_yolo.setChecked(True)
        self.enable_face = QCheckBox('启用低头/视线粗判（MediaPipe）')
        self.enable_face.setChecked(True)

        form.addRow(_form_label('检测开关'), self.enable_camera)
        form.addRow(QLabel(''), self.enable_face)
        form.addRow(QLabel(''), self.enable_yolo)

        card_layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.stats_btn = QPushButton('查看统计')
        self.stats_btn.setObjectName('Ghost')
        _ensure_button_text_visible(self.stats_btn)
        self.stats_btn.clicked.connect(self.stats_requested.emit)
        buttons.addWidget(self.stats_btn)
        buttons.addStretch(1)
        self.start_btn = QPushButton('开始任务')
        _ensure_button_text_visible(self.start_btn)
        buttons.addWidget(self.start_btn)
        card_layout.addLayout(buttons)

        root.addWidget(card)
        root.addStretch(1)

        self.start_btn.clicked.connect(self._on_start)

        self._reload_templates()

    def _reload_templates(self) -> None:
        self.template_select.clear()
        names = [t.name for t in self._templates.list_templates()]
        if not names:
            self.template_select.addItem('（暂无模板）')
            self.template_select.setEnabled(False)
            self.apply_template_btn.setEnabled(False)
            self.delete_template_btn.setEnabled(False)
            return

        self.template_select.setEnabled(True)
        self.apply_template_btn.setEnabled(True)
        self.delete_template_btn.setEnabled(True)
        self.template_select.addItems(names)

    def _on_apply_template(self) -> None:
        if not self.template_select.isEnabled():
            return

        name = (self.template_select.currentText() or '').strip()
        if not name or name.startswith('（'):
            return

        tpl = self._templates.get_template(name)
        if tpl is None:
            QMessageBox.warning(self, '提示', '模板不存在或已损坏。')
            self._reload_templates()
            return

        self.process_whitelist.setPlainText('\n'.join(tpl.allowed_process_names))
        self.title_keywords.setPlainText('\n'.join(tpl.allowed_title_keywords))

    def _on_save_template(self) -> None:
        name = self.template_name.text().strip()
        if not name:
            QMessageBox.warning(self, '提示', '请先填写模板名称。')
            return

        processes = normalize_lines([self.process_whitelist.toPlainText()])
        keywords = normalize_lines([self.title_keywords.toPlainText()])
        if not processes and not keywords:
            QMessageBox.warning(self, '提示', '白名单为空：至少填写进程名或标题关键词再保存。')
            return

        if self._templates.has_template(name):
            ok = QMessageBox.question(self, '覆盖模板？', f'模板「{name}」已存在，是否覆盖？')
            if ok != QMessageBox.StandardButton.Yes:
                return

        try:
            self._templates.upsert_template(name=name, allowed_process_names=processes, allowed_title_keywords=keywords)
        except Exception as exc:
            QMessageBox.warning(self, '保存失败', f'保存模板失败：{exc}')
            return

        self.template_name.setText('')
        self._reload_templates()

    def _on_delete_template(self) -> None:
        if not self.template_select.isEnabled():
            return

        name = (self.template_select.currentText() or '').strip()
        if not name or name.startswith('（'):
            return

        ok = QMessageBox.question(self, '删除模板？', f'确定删除模板「{name}」？')
        if ok != QMessageBox.StandardButton.Yes:
            return

        try:
            self._templates.delete_template(name)
        except Exception as exc:
            QMessageBox.warning(self, '删除失败', f'删除模板失败：{exc}')
            return

        self._reload_templates()

    def _on_start(self) -> None:
        name = self.task_name.text().strip()
        if not name:
            QMessageBox.warning(self, '提示', '请先填写任务名称。')
            return

        start_at = self.start_at.dateTime().toPython()
        end_at = self.end_at.dateTime().toPython()
        if end_at <= start_at:
            QMessageBox.warning(self, '提示', '结束时间需要晚于开始时间。')
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
