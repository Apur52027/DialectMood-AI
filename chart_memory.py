"""Persistent chat memory (own SQLite file, independent of database.py)."""

import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_memory.db")


def _conn():
    return sqlite3.connect(DB_PATH)


def init_chat_db():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages (user_id, id)")


def save_messages(user_id, messages):
    """messages: list of {"role": ..., "content": ...}"""
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as conn:
        conn.executemany(
            "INSERT INTO chat_messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            [(str(user_id), m["role"], m["content"], now) for m in messages],
        )


def load_messages(user_id, limit=200):
    """Return the latest `limit` messages, oldest first."""
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM (
                SELECT id, role, content FROM chat_messages
                WHERE user_id = ? ORDER BY id DESC LIMIT ?
            ) ORDER BY id ASC
            """,
            (str(user_id), limit),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in rows]


def clear_messages(user_id):
    with _conn() as conn:
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (str(user_id),))