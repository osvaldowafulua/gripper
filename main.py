import sys
import os
import platform
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from app.main_window import MainWindow
from app.logging_config import setup_logging


def main():
    app = None
    try:
        setup_logging()
        app = QApplication(sys.argv)
        w = MainWindow()
        w.show()
        sys.exit(app.exec())
    except Exception:
        home = os.path.expanduser("~")
        sysname = platform.system()
        if sysname == "Darwin":
            log_dir = os.path.join(home, "Library", "Logs", "Gripper")
        elif sysname == "Windows":
            base = os.environ.get("LOCALAPPDATA") or home
            log_dir = os.path.join(base, "Gripper", "Logs")
        else:
            log_dir = os.path.join(home, ".local", "share", "gripper", "logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "app.log"), "a", encoding="utf-8") as f:
                f.write("\n=== Crash ===\n")
                f.write(traceback.format_exc())
        except Exception:
            pass
        try:
            if QApplication.instance() is not None:
                QMessageBox.critical(None, "Gripper — Erro ao iniciar", f"A aplicação encontrou um erro ao abrir. Um log foi salvo em {os.path.join(log_dir, 'app.log')}")
        except Exception:
            pass
        # Evita abort do Qt por mensagem modal quando não há contexto GUI
        return 1


if __name__ == "__main__":
    main()
