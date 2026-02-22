def industrial_dark_stylesheet():
    return """
    QWidget {
        background: #0f1318;
        color: #e8eef2;
        font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    }
    QTabWidget::pane { border: 1px solid #26323b; background: #121921; }
    QTabBar::tab { background: #182029; color:#e8eef2; padding:8px 14px; margin:2px; border:1px solid #26323b; border-radius:8px; }
    QTabBar::tab:selected { border-color:#355069; }

    /* Buttons */
    QPushButton { background: #182029; border:2px solid #26323b; color:#e8eef2; padding:10px 16px; border-radius:10px; font-weight:800; text-transform: uppercase; }
    QPushButton:hover { border-color:#355069; }
    QPushButton#btnStart { background:qlineargradient( x1:0 y1:0, x2:0 y2:1, stop:0 #0f6d31, stop:1 #0b4f24); border-color:#13a34b; color:#eaffee }
    QPushButton#btnStop { background:qlineargradient( x1:0 y1:0, x2:0 y2:1, stop:0 #7f0f1f, stop:1 #5b0b17); border-color:#ff3b52; color:#fff3f4 }
    QPushButton#btnReset { background:qlineargradient( x1:0 y1:0, x2:0 y2:1, stop:0 #6a4c0c, stop:1 #4b3609); border-color:#ffb300; color:#fff7e0 }
    QPushButton#btnEmg { background:qlineargradient( x1:0 y1:0, x2:0 y2:1, stop:0 #7f0f1f, stop:1 #5b0b17); border-color:#ff3b52; color:#fff3f4 }
    QPushButton[round="true"] { min-width:84px; min-height:84px; max-width:84px; max-height:84px; padding:0; border-radius:42px; font-size:26px }

    /* Panels */
    QFrame#panel { background: qlineargradient(x1:0 y1:0, x2:0 y2:1, stop:0 #182029, stop:1 #121921); border:1px solid #26323b; border-radius:10px; padding:12px; }
    QLabel.section { color:#90a4ae; letter-spacing: 0.08em; text-transform: uppercase; font-size:12px; margin:4px 0 8px 2px; }

    /* Lamps */
    QLabel[lamp="true"] { width:22px; height:22px; min-width:22px; min-height:22px; max-width:22px; max-height:22px; border-radius:11px; background:#2b3640; border:2px solid rgba(0,0,0,0.2); }
    QLabel[lampType="ready"][on="true"] { background:#00e676; }
    QLabel[lampType="run"][on="true"] { background:#00b0ff; }
    QLabel[lampType="stop"][on="true"] { background:#ff1744; }
    QLabel[lampType="lock"][on="true"] { background:#ffb300; }

    /* IO tiles */
    QLabel#tile { background: rgba(255,255,255,0.02); border:1px solid #26323b; border-radius:8px; padding:8px; }
    QLabel#tile[on="true"] { border-color:#2a7a2a; }
    """
