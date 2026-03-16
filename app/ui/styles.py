def app_stylesheet() -> str:
    return """
    QWidget#Root {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 #BFE9FF,
            stop:0.5 #CFF7D0,
            stop:1 #FFF1B5
        );
        color: #102A43;
        font-family: "Segoe UI", "Microsoft YaHei UI";
        font-size: 14px;
    }
    QLabel#Title {
        font-size: 22px;
        font-weight: 700;
        color: #102A43;
    }
    QLabel#SubTitle {
        font-size: 12px;
        color: rgba(16,42,67,0.75);
    }
    QLineEdit, QTextEdit, QDateTimeEdit, QSpinBox {
        background: rgba(255,255,255,0.75);
        border: 1px solid rgba(16,42,67,0.18);
        border-radius: 10px;
        padding: 8px;
    }
    QPushButton {
        background: rgba(16,42,67,0.9);
        color: white;
        border: 0;
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: 600;
    }
    QPushButton:hover { background: rgba(16,42,67,0.82); }
    QPushButton:pressed { background: rgba(16,42,67,0.75); }
    QPushButton#Ghost {
        background: rgba(255,255,255,0.55);
        color: #102A43;
        border: 1px solid rgba(16,42,67,0.18);
    }
    QPushButton#Ghost:hover { background: rgba(255,255,255,0.7); }
    """

