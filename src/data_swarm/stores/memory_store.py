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
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS role_notes (
                    id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL,
                    tactic TEXT NOT NULL,
                    source_task_id TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS org_playbooks (
                    id INTEGER PRIMARY KEY,
                    topic TEXT NOT NULL,
                    note TEXT NOT NULL,
                    source_task_id TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS personal_preferences (
                    id INTEGER PRIMARY KEY,
                    preference_key TEXT NOT NULL,
                    preference_value TEXT NOT NULL,
                    source_task_id TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def add_role_note(self, role: str, tactic: str, task_id: str) -> None:
        """Add de-identified role note."""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO role_notes(role, tactic, source_task_id) VALUES (?, ?, ?)",
                (role, tactic, task_id),
            )

    def add_org_playbook(self, topic: str, note: str, task_id: str) -> None:
        """Store role-level organizational guidance."""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO org_playbooks(topic, note, source_task_id) VALUES (?, ?, ?)",
                (topic, note, task_id),
            )

    def add_personal_preference(self, key: str, value: str, task_id: str) -> None:
        """Store optional de-identified preference note."""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO personal_preferences(preference_key, preference_value, source_task_id) VALUES (?, ?, ?)",
                (key, value, task_id),
            )
