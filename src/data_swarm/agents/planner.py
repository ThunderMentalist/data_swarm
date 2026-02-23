"""Planner agent."""

from __future__ import annotations

from data_swarm.agents.base import AgentResult, BaseAgent


class PlannerAgent(BaseAgent):
    """Produce a minimal plan document."""

    name = "planner"

    def run(self, title: str) -> AgentResult:
        """Build plan summary text."""
        plan = (
            f"Plan for: {title}\n"
            "1. Validate requirements\n"
            "2. Execute staged workflow\n"
            "3. Review outputs"
        )
        return AgentResult(content=plan, confidence=0.8)
