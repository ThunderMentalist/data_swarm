"""Navigation concierge agent."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone


class NavigationConciergeAgent:
    """Navigation Concierge Agent."""

    name = "Navigation Concierge Agent"

    def next_questions(self) -> list[str]:
        """Return targeted navigation questions."""
        return [
            "Who should be contacted first?",
            "What sequencing constraints matter most?",
            "What risks should this sequence mitigate?",
        ]

    @staticmethod
    def snapshot(content: str) -> dict[str, str]:
        """Create markdown snapshot."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "content": content,
        }

    @staticmethod
    def apply_edits(content: str, notes: str) -> str:
        """Append optional user revision block."""
        if not notes.strip():
            return content
        return content.rstrip() + "\n\n## HITL Navigation Notes\n" + notes.strip() + "\n"
