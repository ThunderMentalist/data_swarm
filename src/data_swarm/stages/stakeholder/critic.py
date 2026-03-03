"""Stakeholder critic agent."""

from __future__ import annotations


class StakeholderCriticAgent:
    """Stakeholder Critic Agent."""

    name = "Stakeholder Critic Agent"

    def evaluate(self, initial_yaml: str, final_yaml: str) -> dict:
        """Evaluate stakeholder mapping output."""
        return {
            "strengths": ["Stakeholder map captured in structured YAML."],
            "gaps": ["Prioritization rationale could be stronger."],
            "suggestions": [
                {
                    "title": "Add stakeholder engagement cadence",
                    "rationale": "Cadence clarifies follow-up expectations.",
                    "evidence": f"Initial length={len(initial_yaml)} Final length={len(final_yaml)}",
                    "suggestion_key": "stakeholder_engagement_cadence",
                }
            ],
        }
