"""Feedback ingestion agent."""

from __future__ import annotations

from dataclasses import dataclass

from data_swarm.tools.io import UserIO
from data_swarm.tools.redaction import sanitize_feedback


@dataclass
class FeedbackSummary:
    """Structured, sanitized feedback payload."""

    sanitized_text: str
    facts_learned: list[str]
    decisions_made: list[str]
    open_questions: list[str]
    commitments: list[str]
    blockers: list[str]
    sentiment: str
    roles_used: list[str]


class FeedbackAgent:
    """Extract de-identified feedback summary."""

    name = "feedback"

    def run(self, text: str, io: UserIO) -> FeedbackSummary:
        """Sanitize text and extract structured content using deterministic heuristics."""
        sanitized_text, roles_used = sanitize_feedback(text, io)
        sentences = [s.strip() for s in sanitized_text.replace("\n", " ").split(".") if s.strip()]

        facts = [s for s in sentences if any(k in s.lower() for k in ["is", "are", "was", "were", "observed"])][:5]
        decisions = [s for s in sentences if any(k in s.lower() for k in ["decided", "approved", "chose"])][:5]
        questions = [s for s in sentences if "?" in s or "question" in s.lower()][:5]
        commitments = [s for s in sentences if any(k in s.lower() for k in ["will", "commit", "by "])][:5]
        blockers = [s for s in sentences if any(k in s.lower() for k in ["blocked", "risk", "issue", "delay"])][:5]

        low = sanitized_text.lower()
        if any(k in low for k in ["great", "thanks", "support"]):
            sentiment = "supportive"
        elif any(k in low for k in ["oppose", "reject", "resist"]):
            sentiment = "resistant"
        elif any(k in low for k in ["confused", "unclear", "not sure"]):
            sentiment = "confused"
        else:
            sentiment = "neutral"

        return FeedbackSummary(
            sanitized_text=sanitized_text,
            facts_learned=facts,
            decisions_made=decisions,
            open_questions=questions,
            commitments=commitments,
            blockers=blockers,
            sentiment=sentiment,
            roles_used=sorted(roles_used),
        )
