from __future__ import annotations


def app_stylesheet() -> str:
    return """
    QWidget#Root {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 #BFE9FF,
            stop:0.5 #CFF7D0,
            stop:1 #FFF1B5
        );
        color: #FFFFFF;
        font-family: "Segoe UI", "Microsoft YaHei UI";
        font-size: 14px;
    }

    QLabel#Title {
        font-size: 27px;
        font-weight: 700;
        color: #FFFFFF;
    }

    QLabel#SubTitle {
        font-size: 17px;
        color: #FFFFFF;
    }

    QLabel#FormLabel, QLabel#InlineLabel {
        background: rgba(0,0,0,0.70);
        color: #FFFFFF;
        border-radius: 8px;
        padding: 6px 10px;
    }

    QFrame#Card {
        background: rgba(0,0,0,0.60);
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 16px;
    }

    QLabel#PreviewBox {
        background: rgba(0,0,0,0.60);
        border: 1px solid rgba(255,255,255,0.20);
        border-radius: 12px;
        color: rgba(255,255,255,0.88);
    }

    QLineEdit, QTextEdit, QDateTimeEdit, QSpinBox, QComboBox, QDateEdit {
        background: rgba(0,0,0,0.60);
        color: #FFFFFF;
        border: 1px solid rgba(255,255,255,0.22);
        border-radius: 10px;
        padding: 8px 10px;
        min-height: 36px;
    }

    QLineEdit:hover, QTextEdit:hover, QDateTimeEdit:hover, QSpinBox:hover, QComboBox:hover, QDateEdit:hover {
        background: rgba(0,0,0,0.45);
        border: 1px solid rgba(255,255,255,0.30);
    }

    QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {
        border: 1px solid rgba(255,255,255,0.45);
    }

    QLineEdit::placeholder, QTextEdit::placeholder {
        color: rgba(255,255,255,0.78);
    }

    QComboBox::drop-down {
        width: 34px;
        border-left: 1px solid rgba(255,255,255,0.16);
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
    }

    QComboBox::drop-down:hover {
        background: rgba(255,255,255,0.08);
    }

    QComboBox QAbstractItemView {
        background: rgba(0,0,0,0.82);
        color: #FFFFFF;
        border: 1px solid rgba(255,255,255,0.18);
        selection-background-color: rgba(255,255,255,0.18);
        selection-color: #FFFFFF;
        outline: 0;
    }

    QComboBox#KeepLight {
        background: rgba(255,255,255,0.75);
        color: #102A43;
        border: 1px solid rgba(16,42,67,0.18);
    }

    QComboBox#KeepLight:hover {
        background: rgba(255,255,255,0.85);
    }

    QComboBox#KeepLight::drop-down {
        border-left: 1px solid rgba(16,42,67,0.18);
    }

    QComboBox#KeepLight::drop-down:hover {
        background: rgba(16,42,67,0.06);
    }

    QComboBox#KeepLight QAbstractItemView {
        background: rgba(255,255,255,0.95);
        color: #102A43;
        border: 1px solid rgba(16,42,67,0.18);
        selection-background-color: rgba(16,42,67,0.10);
        selection-color: #102A43;
        outline: 0;
    }

    QPushButton {
        background: rgba(0,0,0,0.75);
        color: white;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 600;
        min-height: 38px;
    }

    QPushButton:hover { background: rgba(0,0,0,0.60); }
    QPushButton:pressed { background: rgba(0,0,0,0.52); }

    QPushButton:disabled {
        background: rgba(0,0,0,0.35);
        color: rgba(255,255,255,0.60);
        border: 1px solid rgba(255,255,255,0.08);
    }

    QPushButton#Ghost {
        background: rgba(0,0,0,0.45);
        color: #FFFFFF;
        border: 1px solid rgba(255,255,255,0.20);
    }

    QPushButton#Ghost:hover { background: rgba(0,0,0,0.32); }

    QCheckBox {
        color: #FFFFFF;
        spacing: 8px;
    }

    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid rgba(255,255,255,0.35);
        background: rgba(0,0,0,0.45);
    }

    QCheckBox::indicator:hover {
        background: rgba(0,0,0,0.30);
        border: 1px solid rgba(255,255,255,0.45);
    }

    QCheckBox::indicator:checked {
        background: rgba(255,255,255,0.28);
    }

    QTableWidget {
        background: rgba(0,0,0,0.60);
        color: #FFFFFF;
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 12px;
        gridline-color: rgba(255,255,255,0.10);
        selection-background-color: rgba(255,255,255,0.18);
        selection-color: #FFFFFF;
        alternate-background-color: rgba(255,255,255,0.06);
    }

    QTableWidget::item:hover {
        background: rgba(255,255,255,0.10);
    }

    QHeaderView::section {
        background: rgba(0,0,0,0.70);
        color: #FFFFFF;
        padding: 8px 10px;
        border: 0;
        border-right: 1px solid rgba(255,255,255,0.10);
        border-bottom: 1px solid rgba(255,255,255,0.10);
    }

    QHeaderView::section:hover {
        background: rgba(0,0,0,0.55);
    }
    """


def apply_app_palette(app) -> None:
    from PySide6.QtGui import QColor, QPalette

    p = app.palette()
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(255, 255, 255, 200))
    app.setPalette(p)
