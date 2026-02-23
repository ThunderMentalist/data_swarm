"""Stakeholder map scaffold agent."""

from __future__ import annotations

from data_swarm.agents.base import AgentResult, BaseAgent


class StakeholderMapAgent(BaseAgent):
    """Create placeholder stakeholder map."""

    name = "stakeholder_map"

    def run(self) -> AgentResult:
        """Return role-only stakeholder map YAML."""
        content = (
            "roles:\n"
            "  - role: Client Lead\n"
            "    influence: high\n"
            "    interest: high\n"
            "    approach: Keep weekly updates"
        )
        return AgentResult(content=content)
