"""Shared SQLite connection helpers."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DB_FILENAME = "data.db"


def _data_dir() -> Path:
    return Path(os.environ.get("GLANCE_HOME", Path.home() / ".glance"))


def get_db_path() -> Path:
    d = _data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / DB_FILENAME


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn
