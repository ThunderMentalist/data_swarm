"""Deprecated triage agent shim."""

from __future__ import annotations

from data_swarm.agents.base import AgentResult, BaseAgent


class TriageAgent(BaseAgent):
    """Deprecated; use TriageStage instead."""

    name = "triage"

    def run(self, description: str) -> AgentResult:
        """Return compatibility message without confidence-based logic."""
        _ = description
        return AgentResult(content="Deprecated; use TriageStage", confidence=0.5)
