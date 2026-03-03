"""Comms concierge agent."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone


class CommsConciergeAgent:
    """Comms Concierge Agent."""

    name = "Comms Concierge Agent"

    @staticmethod
    def snapshot(payload: dict[str, str]) -> dict:
        """Create comms payload snapshot."""
        serialized = "\n".join(f"{k}:{v}" for k, v in sorted(payload.items()))
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content_hash": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            "payload": payload,
        }
