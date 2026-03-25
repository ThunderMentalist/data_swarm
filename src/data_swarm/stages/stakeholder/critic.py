"""Stakeholder critic agent."""

from __future__ import annotations

from data_swarm.stages.policy_store import PolicyPack


class StakeholderCriticAgent:
    name = "Stakeholder Critic Agent"

    def evaluate(self, initial_payload: dict, final_payload: dict, policy: PolicyPack) -> dict:
        roles = final_payload.get("roles", [])
        missing = [r.get("role", "unknown") for r in roles if not r.get("decision_rights")]
        return {
            "strengths": ["Stakeholder map captured in structured JSON.", f"Policy cards considered: {len(policy.behaviour_cards)}"],
            "gaps": ([f"Missing decision rights for: {', '.join(missing)}"] if missing else ["No major structural gaps detected."]),
            "compliance_score": 100 - (10 * len(missing)),
            "suggestions": [{"title": "Add stakeholder engagement cadence", "rationale": "Cadence clarifies follow-up expectations.", "evidence": f"roles={len(roles)}", "suggestion_key": "stakeholder_engagement_cadence"}],
        }
