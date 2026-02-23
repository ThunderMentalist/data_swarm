"""Feedback ingestion agent."""

from __future__ import annotations

from data_swarm.agents.base import AgentResult, BaseAgent
from data_swarm.tools.redaction import redact_identifiers


class FeedbackAgent(BaseAgent):
    """Extract de-identified feedback summary."""

    name = "feedback"

    def run(self, text: str) -> AgentResult:
        return AgentResult(content=redact_identifiers(text))
