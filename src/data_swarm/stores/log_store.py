"""JSONL and text logging for task runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MASK_KEYS = {"openai_api_key", "api_key", "authorization"}


class LogStore:
    """Persist events and run logs."""

    def __init__(self, task_root: Path) -> None:
        self.log_dir = task_root / "08_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.log_dir / "events.jsonl"
        self.run_log_path = self.log_dir / "run.log"

    def _mask(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {k: ("***" if k.lower() in MASK_KEYS else v) for k, v in payload.items()}

    def event(
        self,
        task_id: str,
        stage: str,
        event_type: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Write JSONL event."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "stage": stage,
            "event_type": event_type,
            "message": message,
            "data": self._mask(data or {}),
        }
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

    def run_log(self, message: str) -> None:
        """Append human-readable run log line."""
        with self.run_log_path.open("a", encoding="utf-8") as f:
            f.write(message + "\n")
