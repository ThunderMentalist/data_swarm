"""Triage agent."""

from __future__ import annotations

from data_swarm.agents.base import AgentResult, BaseAgent


class TriageAgent(BaseAgent):
    """Create basic triage output."""

    name = "triage"

    def run(self, description: str) -> AgentResult:
        questions: list[str] = []
        if len(description.strip()) < 40:
            questions.append("Please provide more implementation context.")
        confidence = 0.4 if questions else 0.8
        return AgentResult(content="\n".join(questions), confidence=confidence)
