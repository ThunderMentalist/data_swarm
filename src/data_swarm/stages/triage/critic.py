"""Triage critic agent."""

from __future__ import annotations

from data_swarm.stages.policy_store import PolicyPack
from data_swarm.stages.triage.models import TaskBrief


class TriageCriticAgent:
    name = "Triage Critic Agent"

    def evaluate(self, initial_brief: TaskBrief, final_brief: TaskBrief, policy: PolicyPack) -> dict:
        required = ["goal", "deliverable", "audience", "success_criteria"]
        missing = [field for field in required if not getattr(final_brief, field)]
        checks = [f"core_prompt_present={bool(policy.core_prompt.strip())}", f"cards={len(policy.behaviour_cards)}"]
        return {
            "strengths": ["Brief captured structured intent."] if not missing else ["Brief has baseline structure."],
            "gaps": missing or ["No major structural gaps detected."],
            "compliance_score": 100 - 20 * len(missing),
            "policy_checks": checks,
            "suggestions": [{"title": "Require full brief completeness", "rationale": "Downstream stages need complete brief fields.", "evidence": f"missing={','.join(missing) or 'none'}", "suggestion_key": "triage_brief_completeness"}],
        }
