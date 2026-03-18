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

    def get_role_notes(self, role: str) -> list[dict[str, str]]:
        """Return role note rows for a role token."""
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute("SELECT role, tactic, source_task_id, created_at FROM role_notes WHERE role = ? ORDER BY id DESC", (role,))
            return [{"role": r[0], "tactic": r[1], "source_task_id": r[2], "created_at": r[3]} for r in cur.fetchall()]

    def search_org_playbooks(self, topic_substr: str) -> list[dict[str, str]]:
        """Find playbooks by topic substring."""
        q = f"%{topic_substr}%"
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute("SELECT topic, note, source_task_id, created_at FROM org_playbooks WHERE topic LIKE ? ORDER BY id DESC", (q,))
            return [{"topic": r[0], "note": r[1], "source_task_id": r[2], "created_at": r[3]} for r in cur.fetchall()]

    def get_personal_preferences(self, key_prefix: str | None = None) -> dict[str, str]:
        """Get preference map (optionally by key prefix)."""
        with sqlite3.connect(self.path) as conn:
            if key_prefix:
                cur = conn.execute("SELECT preference_key, preference_value FROM personal_preferences WHERE preference_key LIKE ? ORDER BY id DESC", (f"{key_prefix}%",))
            else:
                cur = conn.execute("SELECT preference_key, preference_value FROM personal_preferences ORDER BY id DESC")
            out: dict[str, str] = {}
            for k, v in cur.fetchall():
                out.setdefault(k, v)
            return out

    def list_recent_role_notes(self, limit: int = 10) -> list[dict[str, str]]:
        """Return recent role notes."""
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute("SELECT role, tactic, source_task_id, created_at FROM role_notes ORDER BY id DESC LIMIT ?", (limit,))
            return [{"role": r[0], "tactic": r[1], "source_task_id": r[2], "created_at": r[3]} for r in cur.fetchall()]
