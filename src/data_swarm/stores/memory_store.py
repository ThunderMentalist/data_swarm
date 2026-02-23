"""Local de-identified memory store."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class MemoryStore:
    """SQLite memory store for role-level learnings only."""

    def __init__(self, home: Path) -> None:
        self.path = home / "memory" / "memory.sqlite"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS role_notes (
                    id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL,
                    tactic TEXT NOT NULL,
                    source_task_id TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_role_note(self, role: str, tactic: str, task_id: str) -> None:
        """Add de-identified role note."""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO role_notes(role, tactic, source_task_id) VALUES (?, ?, ?)",
                (role, tactic, task_id),
            )
