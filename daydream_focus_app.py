from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QObject, QMetaObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

from pathlib import Path

from app.core.monitor_controller import MonitorController
from app.core.models import TaskConfig
from app.core.session_logger import SessionLogger
from app.io.active_window import WindowsActiveWindowProvider
from app.io.video_source import LocalWebcamSource
from app.ui.alarm_overlay import AlarmOverlay
from app.ui.surrender_overlay import SurrenderOverlay
from app.ui.home_page import HomePage
from app.ui.session_page import SessionPage
from app.ui.stats_page import StatsPage
from app.ui.styles import app_stylesheet, apply_app_palette
from daydream_vision import VisionAnalyzer
from daydream_store import SqliteSessionRecorder


def _now_local() -> datetime:
    return datetime.now().astimezone()


class _NullActiveWindowProvider:
    def get_foreground_app(self):
        return None


class _Worker(QObject):
    ticked = Signal(object, object)  # (StateUpdate, frame_bgr)
    failed = Signal(str)

    def __init__(self, config: TaskConfig):
        super().__init__()
        self._config = config
        self._timer: QTimer | None = None

        self._video = None
        self._vision = None
        self._active_window = None
        self._monitor = None
        self._logger = None
        self._db = None

    @Slot()
    def start(self) -> None:
        self._timer = QTimer(self)
        self._timer.setInterval(self._config.sample_interval_ms)
        self._timer.timeout.connect(self._on_tick)

        try:
            self._active_window = WindowsActiveWindowProvider()
        except Exception:
            self._active_window = _NullActiveWindowProvider()

        enable_yolo = self._config.enable_yolo_phone and self._config.enable_camera
        if enable_yolo and not Path("yolov8n.pt").exists():
            enable_yolo = False
            self.failed.emit("未找到 yolov8n.pt，已跳过手机检测（YOLOv8）。")

        self._vision = VisionAnalyzer(
            enable_face_pose=self._config.enable_face_pose and self._config.enable_camera,
            enable_yolo_phone=enable_yolo,
        )

        started_at = _now_local()
        self._logger = SessionLogger(self._config.task_name, started_at=started_at)
        try:
            self._db = SqliteSessionRecorder(
                db_path=Path("data") / "daydream_focus.sqlite3",
                config=self._config,
                started_at=started_at,
            )
        except Exception as exc:
            self._db = None
            self.failed.emit(f"SQLite 记录初始化失败：{exc}")

        effective_config = self._config

        if self._config.enable_camera:
            try:
                self._video = LocalWebcamSource(0)
                self._video.open()
            except Exception as exc:
                self._video = None
                self.failed.emit(f"摄像头打开失败：{exc}（已切换为仅窗口检测模式）")
                effective_config = self._config.model_copy(
                    update={"enable_camera": False, "enable_yolo_phone": False, "enable_face_pose": False}
                )

        self._config = effective_config

        def _on_update(update):
            if self._logger is not None:
                self._logger.on_update(update)
            if self._db is not None:
                self._db.on_update(update)

        self._monitor = MonitorController(
            config=self._config,
            active_window_provider=self._active_window,
            vision_analyzer=self._vision if self._config.enable_camera else None,
            on_update=_on_update,
        )

        self._timer.start()

    @Slot()
    def stop(self) -> None:
        try:
            if self._timer is not None:
                self._timer.stop()
        except Exception:
            pass

        try:
            if self._video is not None:
                self._video.close()
        except Exception:
            pass

        if self._logger is not None:
            ended_at = _now_local()
            self._logger.finalize(ended_at)
            try:
                self._logger.export_json()
                self._logger.export_csv()
            except Exception:
                pass

            if self._db is not None:
                try:
                    self._db.finalize(ended_at)
                except Exception:
                    pass

    def _on_tick(self) -> None:
        frame = None
        if self._video is not None:
            frame = self._video.read()

        if self._monitor is None:
            return
        update = self._monitor.tick(frame_bgr=frame)
        self.ticked.emit(update, frame)


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daydream Focus")
        self.setMinimumSize(980, 640)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._home = HomePage()
        self._session = SessionPage()
        self._stats = StatsPage()
        self._stack.addWidget(self._home)
        self._stack.addWidget(self._session)
        self._stack.addWidget(self._stats)

        self._overlay = AlarmOverlay()

        self._surrender = SurrenderOverlay()

        self._home.start_requested.connect(self._start_session)
        self._home.stats_requested.connect(self._show_stats)
        self._session.exit_requested.connect(self._confirm_exit)
        self._stats.back_requested.connect(self._back_home)

        self._worker_thread: QThread | None = None
        self._worker: _Worker | None = None

        self._config: TaskConfig | None = None
        self._started_at: datetime | None = None

        self._schedule_timer = QTimer(self)
        self._schedule_timer.setInterval(500)
        self._schedule_timer.timeout.connect(self._schedule_tick)

    def _start_session(self, config: TaskConfig) -> None:
        self._config = config
        self._started_at = None

        self._session.set_config(config)
        self._stack.setCurrentWidget(self._session)
        self._overlay.hide_overlay()

        self._schedule_timer.start()

    def _schedule_tick(self) -> None:
        if self._config is None:
            return

        now = _now_local()
        if now >= self._config.end_at:
            self._stop_and_back_home()
            return

        if now < self._config.start_at:
            return

        if self._worker is None:
            self._started_at = now
            self._session.mark_started(now)
            self._start_worker(self._config)

    def _start_worker(self, config: TaskConfig) -> None:
        self._worker_thread = QThread(self)
        self._worker = _Worker(config)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.start)
        self._worker.ticked.connect(self._on_worker_ticked)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker_thread.start()

    def _on_worker_failed(self, message: str) -> None:
        self.statusBar().showMessage(message, 8000)

    def _on_worker_ticked(self, update, frame_bgr) -> None:
        self._session.on_state_update(update)
        if frame_bgr is not None:
            self._session.set_preview_frame(frame_bgr)

        if update.alarm_on:
            self._overlay.show_overlay()
        else:
            self._overlay.hide_overlay()

    def _confirm_exit(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle('退出？')
        box.setText('确定要中道崩殂嘛bro？')
        yes_btn = box.addButton('yes', QMessageBox.ButtonRole.YesRole)
        no_btn = box.addButton('no', QMessageBox.ButtonRole.NoRole)
        box.setDefaultButton(no_btn)
        box.exec()

        if box.clickedButton() == yes_btn:
            self._surrender_and_back_home()

    def _stop_session(self) -> None:
        self._schedule_timer.stop()
        self._overlay.hide_overlay()
        try:
            self._surrender.hide_overlay()
        except Exception:
            pass

        if self._worker is not None:
            try:
                QMetaObject.invokeMethod(self._worker, 'stop', Qt.ConnectionType.QueuedConnection)
            except Exception:
                pass

        if self._worker_thread is not None:
            self._worker_thread.quit()
            self._worker_thread.wait(2000)

        self._worker_thread = None
        self._worker = None
        self._config = None
        self._started_at = None

    def _surrender_and_back_home(self) -> None:
        self._stop_session()
        self._surrender.show_for(5000, on_finished=self._back_home_after_surrender)

    def _back_home_after_surrender(self) -> None:
        self._stack.setCurrentWidget(self._home)

    def _stop_and_back_home(self) -> None:
        self._stop_session()
        self._stack.setCurrentWidget(self._home)

    def _show_stats(self) -> None:
        self._stack.setCurrentWidget(self._stats)
        try:
            self._stats.refresh()
        except Exception:
            pass

    def _back_home(self) -> None:
        self._stack.setCurrentWidget(self._home)


def run_app() -> None:
    app = QApplication([])
    apply_app_palette(app)
    app.setStyleSheet(app_stylesheet())
    win = AppWindow()
    win.show()
    app.exec()



