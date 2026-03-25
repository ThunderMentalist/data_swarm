"""Planner curator agent."""

from __future__ import annotations

from data_swarm import yaml_compat as yaml
from data_swarm.stages.policy_store import PolicyPack


class PlannerCuratorAgent:
    name = "Planner Curator Agent"

    def curate(self, initial_plan: dict, final_plan: dict, policy: PolicyPack) -> tuple[str, str]:
        delta = "\n".join([
            "# Planner Delta Learning",
            "",
            f"- Initial milestones: {len(initial_plan.get('milestones', []))}",
            f"- Final milestones: {len(final_plan.get('milestones', []))}",
            f"- Policy cards considered: {len(policy.behaviour_cards)}",
        ]) + "\n"
        payload = {"facts": ["Human clarifications improved planning specificity."], "behaviour_cards": [{"title": "Capture explicit success criteria in planning", "guidance": "Ask and record measurable outcomes.", "evidence": ",".join(final_plan.get("success_criteria", []))[:180]}]}
        return delta, yaml.safe_dump(payload, sort_keys=False)
