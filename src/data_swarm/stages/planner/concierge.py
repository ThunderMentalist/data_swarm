"""Planner concierge agent."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone


class PlannerConciergeAgent:
    """Planner Concierge Agent."""

    name = "Planner Concierge Agent"

    @staticmethod
    def initial_plan(title: str) -> str:
        """Create a deterministic initial planning scaffold."""
        return (
            f"Plan for: {title}\n"
            "1. Validate requirements\n"
            "2. Execute staged workflow\n"
            "3. Review outputs"
        )

    def next_questions(self, plan_text: str) -> list[str]:
        """Return targeted planning questions."""
        del plan_text
        return [
            "What is the deadline or milestone timing for this plan?",
            "What measurable success criteria should this plan satisfy?",
            "What key risks or blockers should be planned around?",
            "What dependencies or approvals are required?",
        ]

    def apply_answers(self, plan_text: str, qa_round: list[tuple[str, str]]) -> str:
        """Append HITL notes to current plan."""
        notes = [f"- {q} -> {a.strip() or 'No additional input'}" for q, a in qa_round]
        block = "\n".join(["", "## HITL Notes", *notes])
        if "## HITL Notes" in plan_text:
            return plan_text + "\n" + "\n".join(notes)
        return plan_text.rstrip() + block + "\n"

    @staticmethod
    def snapshot(plan_text: str) -> dict[str, str]:
        """Create history snapshot payload."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content_hash": hashlib.sha256(plan_text.encode("utf-8")).hexdigest(),
            "content": plan_text,
        }

    @staticmethod
    def load_last_snapshot(rows: list[dict]) -> str:
        """Load latest content from history rows."""
        if not rows:
            return ""
        return str(rows[-1].get("content", ""))
