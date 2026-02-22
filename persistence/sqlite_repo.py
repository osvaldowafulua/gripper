import os
import platform
from pathlib import Path
import sqlite3
from typing import Optional
from persistence.json_io import project_to_dict, dict_to_project
from domain.models import ProjectConfig
import json


def _default_db_path():
    home = Path.home()
    sysname = platform.system()
    if sysname == "Darwin":
        d = home / "Library" / "Application Support" / "Gripper"
    elif sysname == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA") or home)
        d = base / "Gripper"
    else:
        d = home / ".local" / "share" / "gripper"
    d.mkdir(parents=True, exist_ok=True)
    return str(d / "gripper.db")


class SQLiteRepo:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or _default_db_path()
        self._ensure()

    def _ensure(self):
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, version TEXT, data TEXT)"
            )
            conn.commit()
        finally:
            conn.close()

    def save_project(self, name: str, cfg: ProjectConfig) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            data = json.dumps(project_to_dict(cfg), ensure_ascii=False)
            cur.execute("INSERT INTO projects(name, version, data) VALUES (?,?,?)", (name, cfg.versao, data))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def load_latest(self) -> Optional[ProjectConfig]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT data FROM projects ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            if not row:
                return None
            data = json.loads(row[0])
            return dict_to_project(data)
        finally:
            conn.close()
