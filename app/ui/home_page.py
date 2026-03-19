from __future__ import annotations

import os

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.core.models import TaskConfig, normalize_lines
from app.core.whitelist_templates import WhitelistTemplateStore
from app.io.video_source import probe_local_webcam


def _form_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName('FormLabel')
    return label


def _ensure_button_text_visible(btn: QPushButton, extra_px: int = 34) -> None:
    btn.setMinimumWidth(btn.fontMetrics().horizontalAdvance(btn.text()) + extra_px)


class CollapsibleSection(QFrame):
    def __init__(self, title: str, content: QWidget, *, collapsed: bool = True):
        super().__init__()
        self.setObjectName('CollapsibleSection')

        self._toggle = QToolButton()
        self._toggle.setObjectName('SectionHeader')
        self._toggle.setText(title)
        self._toggle.setCheckable(True)
        self._toggle.setChecked(not collapsed)
        self._toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toggle.setArrowType(
            Qt.ArrowType.DownArrow if not collapsed else Qt.ArrowType.RightArrow
        )
        self._toggle.clicked.connect(self._on_toggled)

        self._content = content
        self._content.setVisible(not collapsed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self._toggle)
        layout.addWidget(self._content)

    def _on_toggled(self, checked: bool) -> None:
        self._content.setVisible(checked)
        self._toggle.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)


class SliderSpinBox(QWidget):
    def __init__(
        self,
        *,
        minimum: int,
        maximum: int,
        value: int,
        slider_step: int = 10,
        spin_suffix: str = ' 秒',
    ):
        super().__init__()

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(minimum, maximum)
        self.slider.setSingleStep(slider_step)
        self.slider.setPageStep(slider_step)
        self.slider.setValue(value)

        self.spin = QSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.setValue(value)
        self.spin.setSuffix(spin_suffix)

        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        row.addWidget(self.slider, 1)
        row.addWidget(self.spin)

    def value(self) -> int:
        return int(self.spin.value())

    def setValue(self, value: int) -> None:  # noqa: N802 (Qt style)
        self.spin.setValue(int(value))


class ItemListEditor(QWidget):
    def __init__(self, *, placeholder: str):
        super().__init__()

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setMinimumHeight(92)

        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)

        self._add_btn = QPushButton('添加')
        self._add_btn.setObjectName('Ghost')
        _ensure_button_text_visible(self._add_btn, 26)
        self._add_btn.clicked.connect(self._on_add)

        self._remove_btn = QPushButton('删除选中')
        self._remove_btn.setObjectName('Ghost')
        _ensure_button_text_visible(self._remove_btn, 26)
        self._remove_btn.clicked.connect(self._on_remove)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(10)
        input_row.addWidget(self._input, 1)
        input_row.addWidget(self._add_btn)
        input_row.addWidget(self._remove_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self._list)
        layout.addLayout(input_row)

        self._input.returnPressed.connect(self._on_add)

    def items(self) -> list[str]:
        out: list[str] = []
        for i in range(self._list.count()):
            out.append(self._list.item(i).text())
        return out

    def set_items(self, items: list[str]) -> None:
        self._list.clear()
        for item in items:
            s = (item or '').strip()
            if s:
                self._list.addItem(s)

    def _on_add(self) -> None:
        raw = self._input.text().strip()
        if not raw:
            return

        parts = normalize_lines([raw])
        existing = {s.strip() for s in self.items() if s.strip()}
        for part in parts:
            if part not in existing:
                self._list.addItem(part)
                existing.add(part)

        self._input.setText('')

    def _on_remove(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        self._list.takeItem(row)


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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        card = QFrame()
        card.setObjectName('Card')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        # --- Task name (always visible)
        top_form = QFormLayout()
        top_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        top_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        top_form.setVerticalSpacing(10)

        self.task_name = QLineEdit()
        self.task_name.setPlaceholderText('例如：数学作业 / 论文写作 / 刷题')
        top_form.addRow(_form_label('任务名称'), self.task_name)
        card_layout.addLayout(top_form)

        # --- Section: Time & thresholds
        time_box = QWidget()
        time_form = QFormLayout(time_box)
        time_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        time_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        time_form.setVerticalSpacing(10)

        self.start_at = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_at.setCalendarPopup(True)
        self.end_at = QDateTimeEdit(QDateTime.currentDateTime().addSecs(60 * 60))
        self.end_at.setCalendarPopup(True)

        self.duration_preset = QComboBox()
        self.duration_preset.setObjectName('KeepLight')
        self.duration_preset.addItem('15 分钟', 15 * 60)
        self.duration_preset.addItem('30 分钟', 30 * 60)
        self.duration_preset.addItem('1 小时', 60 * 60)
        self.duration_preset.addItem('自定义', None)

        dur_row = QHBoxLayout()
        dur_row.setSpacing(10)
        dur_row.addWidget(self.duration_preset)
        dur_row.addStretch(1)
        dur_container = QWidget()
        dur_container.setLayout(dur_row)

        time_row = QHBoxLayout()
        time_row.setSpacing(10)
        time_row.addWidget(self.start_at)
        arrow = QLabel('→')
        arrow.setObjectName('InlineLabel')
        time_row.addWidget(arrow)
        time_row.addWidget(self.end_at)
        time_container = QWidget()
        time_container.setLayout(time_row)

        time_form.addRow(_form_label('常用时长'), dur_container)
        time_form.addRow(_form_label('起止时间'), time_container)

        self.distract_after = SliderSpinBox(minimum=30, maximum=60 * 60, value=3 * 60)
        time_form.addRow(_form_label('触发阈值'), self.distract_after)

        self.release_after = SliderSpinBox(minimum=10, maximum=60 * 60, value=2 * 60)
        time_form.addRow(_form_label('解除阈值'), self.release_after)

        self.duration_preset.currentIndexChanged.connect(self._sync_end_time)
        self.start_at.dateTimeChanged.connect(self._sync_end_time)
        self._sync_end_time()

        card_layout.addWidget(CollapsibleSection('时间与阈值', time_box, collapsed=False))

        # --- Section: Whitelist & templates
        wl_box = QWidget()
        wl_form = QFormLayout(wl_box)
        wl_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        wl_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        wl_form.setVerticalSpacing(10)

        self.template_select = QComboBox()
        self.apply_template_btn = QPushButton('套用模板')
        self.apply_template_btn.setObjectName('Ghost')
        _ensure_button_text_visible(self.apply_template_btn)
        self.apply_template_btn.clicked.connect(self._on_apply_template)

        tpl_row = QHBoxLayout()
        tpl_row.setSpacing(10)
        tpl_row.addWidget(self.template_select, 1)
        tpl_row.addWidget(self.apply_template_btn)
        tpl_container = QWidget()
        tpl_container.setLayout(tpl_row)
        wl_form.addRow(_form_label('白名单模板'), tpl_container)

        self.process_list = ItemListEditor(
            placeholder='进程名：例如 WINWORD.EXE / chrome.exe / code.exe（回车添加，逗号也可）'
        )
        wl_form.addRow(_form_label('进程白名单'), self.process_list)

        self.keyword_list = ItemListEditor(placeholder='标题关键词：例如 作业 / LeetCode / Notion')
        wl_form.addRow(_form_label('标题关键词'), self.keyword_list)

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
        wl_form.addRow(QLabel(''), tpl_manage_container)

        card_layout.addWidget(CollapsibleSection('白名单与关键词', wl_box, collapsed=True))

        # --- Section: Detection toggles
        toggles_box = QWidget()
        toggles_form = QFormLayout(toggles_box)
        toggles_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        toggles_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        toggles_form.setVerticalSpacing(10)

        self.enable_camera = QCheckBox('启用摄像头检测（建议开启）')
        self.enable_camera.setChecked(True)
        self.enable_face = QCheckBox('启用低头/视线粗判（MediaPipe）')
        self.enable_face.setChecked(True)
        self.enable_yolo = QCheckBox('启用手机检测（YOLOv8，CPU 上可能偏重）')
        self.enable_yolo.setChecked(True)

        toggles_form.addRow(_form_label('检测开关'), self.enable_camera)
        toggles_form.addRow(QLabel(''), self.enable_face)
        toggles_form.addRow(QLabel(''), self.enable_yolo)

        card_layout.addWidget(CollapsibleSection('检测开关', toggles_box, collapsed=True))

        # --- Buttons
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
        self.start_btn.clicked.connect(self._on_start)
        buttons.addWidget(self.start_btn)
        card_layout.addLayout(buttons)

        scroll.setWidget(card)
        root.addWidget(scroll, 1)

        self._reload_templates()

    def _sync_end_time(self) -> None:
        secs = self.duration_preset.currentData()
        if isinstance(secs, int) and secs > 0:
            self.end_at.setEnabled(False)
            self.end_at.setDateTime(self.start_at.dateTime().addSecs(int(secs)))
        else:
            self.end_at.setEnabled(True)

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

        self.process_list.set_items(list(tpl.allowed_process_names))
        self.keyword_list.set_items(list(tpl.allowed_title_keywords))

    def _on_save_template(self) -> None:
        name = self.template_name.text().strip()
        if not name:
            QMessageBox.warning(self, '提示', '请先填写模板名称。')
            return

        processes = normalize_lines(self.process_list.items())
        keywords = normalize_lines(self.keyword_list.items())
        if not processes and not keywords:
            QMessageBox.warning(self, '提示', '白名单为空：至少填写进程名或标题关键词再保存。')
            return

        if self._templates.has_template(name):
            ok = QMessageBox.question(self, '覆盖模板？', f'模板「{name}」已存在，是否覆盖？')
            if ok != QMessageBox.StandardButton.Yes:
                return

        try:
            self._templates.upsert_template(
                name=name,
                allowed_process_names=processes,
                allowed_title_keywords=keywords,
            )
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

        enable_camera = bool(self.enable_camera.isChecked())
        if enable_camera:
            ok = QMessageBox.question(
                self,
                '摄像头权限',
                '需要使用摄像头进行实时专注监测（不保存画面），是否允许？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ok != QMessageBox.StandardButton.Yes:
                enable_camera = False
            else:
                available, err = probe_local_webcam(0)
                if not available:
                    choice = QMessageBox.question(
                        self,
                        '摄像头不可用',
                        f'摄像头打开/取帧失败：{err}\n\n是否打开系统“摄像头隐私设置”？\n（也可以选择继续，以仅窗口检测模式运行）',
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No
                        | QMessageBox.StandardButton.Cancel,
                    )
                    if choice == QMessageBox.StandardButton.Yes:
                        try:
                            os.startfile('ms-settings:privacy-webcam')
                        except Exception:
                            pass
                        return
                    if choice == QMessageBox.StandardButton.Cancel:
                        return
                    enable_camera = False

        if not enable_camera:
            self.enable_camera.setChecked(False)
            self.enable_face.setChecked(False)
            self.enable_yolo.setChecked(False)

        config = (
            TaskConfig(
                task_name=name,
                start_at=start_at,
                end_at=end_at,
                distract_alarm_after_s=int(self.distract_after.value()),
                release_alarm_after_work_s=int(self.release_after.value()),
                allowed_process_names=normalize_lines(self.process_list.items()),
                allowed_title_keywords=normalize_lines(self.keyword_list.items()),
                enable_camera=bool(enable_camera),
                enable_yolo_phone=bool(self.enable_yolo.isChecked()) and bool(enable_camera),
                enable_face_pose=bool(self.enable_face.isChecked()) and bool(enable_camera),
            )
            .normalized()
        )

        self.start_requested.emit(config)
