"""Planner critic agent."""

from __future__ import annotations


class PlannerCriticAgent:
    """Planner Critic Agent."""

    name = "Planner Critic Agent"

    def evaluate(self, initial_plan: str, final_plan: str) -> dict:
        """Generate deterministic post-approval critique payload."""
        strengths = ["Plan has an explicit structure."]
        if "HITL Notes" in final_plan:
            strengths.append("Plan incorporates human feedback.")
        gaps = [] if "success" in final_plan.lower() else ["Success criteria are not explicit in plan body."]
        return {
            "strengths": strengths,
            "gaps": gaps or ["No major structural gaps detected."],
            "suggestions": [
                {
                    "title": "Add explicit acceptance checks",
                    "rationale": "Acceptance checks reduce downstream ambiguity.",
                    "evidence": f"Initial size={len(initial_plan)}, final size={len(final_plan)}",
                    "suggestion_key": "planner_acceptance_checks",
                }
            ],
        }
