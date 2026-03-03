"""Comms concierge agent."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone


class CommsConciergeAgent:
    """Comms Concierge Agent."""

    name = "Comms Concierge Agent"

    @staticmethod
    def initial_email_draft(task_title: str, summary: str, tone_profile: str) -> str:
        """Create a deterministic email draft using tone profile text."""
        tone = tone_profile or "Diplomatic"
        return f"Tone:\n{tone}\n\nEmail Draft:\nHello team,\n\n{task_title}: {summary}\n\nThanks."

    @staticmethod
    def snapshot(payload: dict[str, str]) -> dict:
        """Create comms payload snapshot."""
        serialized = "\n".join(f"{k}:{v}" for k, v in sorted(payload.items()))
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content_hash": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            "payload": payload,
        }
