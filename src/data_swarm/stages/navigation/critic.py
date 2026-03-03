"""Navigation critic agent."""

from __future__ import annotations


class NavigationCriticAgent:
    """Navigation Critic Agent."""

    name = "Navigation Critic Agent"

    def evaluate(self, initial_doc: str, final_doc: str) -> dict:
        """Generate deterministic navigation critique."""
        return {
            "strengths": ["Navigation flow was documented."],
            "gaps": ["Escalation ownership could be clearer."],
            "suggestions": [
                {
                    "title": "Define owner for each outreach step",
                    "rationale": "Clear ownership improves execution speed.",
                    "evidence": f"Doc length moved from {len(initial_doc)} to {len(final_doc)}",
                    "suggestion_key": "navigation_step_owners",
                }
            ],
        }
