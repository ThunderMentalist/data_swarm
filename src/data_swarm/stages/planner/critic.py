"""Planner critic agent."""

from __future__ import annotations

from data_swarm.stages.policy_store import PolicyPack


class PlannerCriticAgent:
    name = "Planner Critic Agent"

    def evaluate(self, initial_plan: dict, final_plan: dict, policy: PolicyPack) -> dict:
        required = [line.split(":", 1)[1].strip() for line in policy.core_prompt.splitlines() if line.startswith("required_section:")]
        missing = [section for section in required if not final_plan.get(section)]
        strengths = ["Plan has explicit objective and milestones."]
        if not missing:
            strengths.append("Plan satisfies policy-required sections.")
        return {
            "strengths": strengths,
            "gaps": missing or ["No major structural gaps detected."],
            "compliance_score": max(0, 100 - 15 * len(missing)),
            "suggestions": [{"title": "Add explicit acceptance checks", "rationale": "Acceptance checks reduce ambiguity.", "evidence": f"missing={','.join(missing) or 'none'}", "suggestion_key": "planner_acceptance_checks"}],
        }
