"""Triage curator agent."""

from __future__ import annotations

from data_swarm import yaml_compat as yaml
from data_swarm.stages.policy_store import PolicyPack
from data_swarm.stages.triage.models import TaskBrief


class TriageCuratorAgent:
    name = "Triage Curator Agent"

    def curate(self, initial_brief: TaskBrief, final_brief: TaskBrief, policy: PolicyPack) -> tuple[str, str]:
        delta = "\n".join([
            "# Triage Delta Learning",
            "",
            f"- Initial constraints: {len(initial_brief.constraints)}",
            f"- Final constraints: {len(final_brief.constraints)}",
            f"- Policy trees considered: {len(policy.decision_trees)}",
        ]) + "\n"
        payload = {
            "facts": ["Brief quality improves with explicit success criteria."],
            "behaviour_cards": [{"title": "Ask for complete brief", "guidance": "Collect goal, deliverable, audience, success criteria every run.", "evidence": str(final_brief.to_dict())[:180]}],
        }
        return delta, yaml.safe_dump(payload, sort_keys=False)
