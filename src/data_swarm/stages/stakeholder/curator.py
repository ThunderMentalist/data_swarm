"""Stakeholder curator agent."""

from __future__ import annotations

from data_swarm import yaml_compat as yaml
from data_swarm.stages.policy_store import PolicyPack


class StakeholderCuratorAgent:
    name = "Stakeholder Curator Agent"

    def curate(self, initial_payload: dict, final_payload: dict, policy: PolicyPack) -> tuple[str, str]:
        delta = (
            "# Stakeholder Delta Learning\n\n"
            f"- Initial roles: {len(initial_payload.get('roles', []))}\n"
            f"- Final roles: {len(final_payload.get('roles', []))}\n"
            f"- Decision trees considered: {len(policy.decision_trees)}\n"
        )
        payload = {"facts": ["Stakeholder mapping improved after review."], "behaviour_cards": [{"title": "Capture stakeholder influence and cadence", "guidance": "Always include influence plus engagement rhythm.", "evidence": str(final_payload.get('roles', []))[:180]}]}
        return delta, yaml.safe_dump(payload, sort_keys=False)
