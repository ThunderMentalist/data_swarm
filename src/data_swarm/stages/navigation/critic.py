"""Navigation critic agent."""

from __future__ import annotations

from data_swarm.stages.policy_store import PolicyPack


class NavigationCriticAgent:
    name = "Navigation Critic Agent"

    def evaluate(self, initial_doc: dict, final_doc: dict, policy: PolicyPack) -> dict:
        missing_escalation = not final_doc.get("escalation_triggers")
        return {
            "strengths": ["Navigation flow was documented.", f"Policy trees considered: {len(policy.decision_trees)}"],
            "gaps": (["Escalation triggers are missing."] if missing_escalation else ["No major structural gaps detected."]),
            "compliance_score": 80 if missing_escalation else 100,
            "suggestions": [{"title": "Define owner for each outreach step", "rationale": "Clear ownership improves execution speed.", "evidence": f"steps={len(final_doc.get('outreach_sequence', []))}", "suggestion_key": "navigation_step_owners"}],
        }
