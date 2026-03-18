"""JSONL and text logging for task runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MASK_KEYS = {"openai_api_key", "api_key", "authorization"}


class LogStore:
    """Persist events and run logs."""

    def __init__(self, task_root: Path, anonymizer: Any | None = None, strict_redaction: bool = False) -> None:
        self.log_dir = task_root / "08_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.log_dir / "events.jsonl"
        self.run_log_path = self.log_dir / "run.log"
        self.anonymizer = anonymizer
        self.strict_redaction = strict_redaction

    def _mask(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {k: ("***" if k.lower() in MASK_KEYS else self._sanitize(v)) for k, v in payload.items()}

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, str) and self.strict_redaction and self.anonymizer is not None:
            return self.anonymizer.sanitize_text(value)[0]
        if isinstance(value, dict):
            return {k: self._sanitize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._sanitize(v) for v in value]
        return value

    def event(self, task_id: str, stage: str, event_type: str, message: str, data: dict[str, Any] | None = None) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "stage": stage,
            "event_type": event_type,
            "message": self._sanitize(message),
            "data": self._mask(data or {}),
        }
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

    def run_log(self, message: str) -> None:
        msg = self._sanitize(message) if self.strict_redaction else message
        with self.run_log_path.open("a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
