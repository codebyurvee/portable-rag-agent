"""Minimal SQLite persistence for query/run metadata (stdlib sqlite3 only)."""

import os
import sqlite3
from datetime import datetime, timezone

DEFAULT_PATH = "database/agent.db"


def _path() -> str:
    return os.getenv("DATABASE_PATH", DEFAULT_PATH)


def connect(path: str | None = None) -> sqlite3.Connection:
    path = path or _path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: str | None = None) -> None:
    with connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS query_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                framework TEXT NOT NULL,
                status TEXT NOT NULL,
                answer TEXT,
                tools_used TEXT
            )
            """
        )


def record_run(query: str, framework: str, status: str, answer: str,
               tools_used: list[str], path: str | None = None) -> int:
    with connect(path) as conn:
        cur = conn.execute(
            """
            INSERT INTO query_runs (timestamp, query, framework, status, answer, tools_used)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                query,
                framework,
                status,
                answer,
                ",".join(tools_used),
            ),
        )
        return cur.lastrowid


def list_runs(path: str | None = None) -> list[dict]:
    with connect(path) as conn:
        rows = conn.execute("SELECT * FROM query_runs ORDER BY id").fetchall()
        return [dict(r) for r in rows]
