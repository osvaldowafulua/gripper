import logging
import os
import platform
from pathlib import Path
from logging.handlers import RotatingFileHandler


def _default_log_path():
    try:
        home = Path.home()
        sysname = platform.system()
        if sysname == "Darwin":
            d = home / "Library" / "Logs" / "Gripper"
        elif sysname == "Windows":
            base = Path(os.environ.get("LOCALAPPDATA") or home)
            d = base / "Gripper" / "Logs"
        else:
            d = home / ".local" / "share" / "gripper" / "logs"
        d.mkdir(parents=True, exist_ok=True)
        return str(d / "app.log")
    except Exception:
        return "gripper.log"


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fh = RotatingFileHandler(_default_log_path(), maxBytes=512000, backupCount=3)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
