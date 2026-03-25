"""Navigation curator agent."""

from __future__ import annotations

from data_swarm import yaml_compat as yaml
from data_swarm.stages.policy_store import PolicyPack


class NavigationCuratorAgent:
    name = "Navigation Curator Agent"

    def curate(self, initial_doc: dict, final_doc: dict, policy: PolicyPack) -> tuple[str, str]:
        delta = (
            "# Navigation Delta Learning\n\n"
            f"- Initial steps: {len(initial_doc.get('outreach_sequence', []))}\n"
            f"- Final steps: {len(final_doc.get('outreach_sequence', []))}\n"
            f"- Policy cards considered: {len(policy.behaviour_cards)}\n"
        )
        payload = {"facts": ["Navigation notes improved sequencing clarity."], "behaviour_cards": [{"title": "Ask sequencing and risk questions", "guidance": "Capture first-contact order and risk mitigations.", "evidence": str(final_doc)[:180]}]}
        return delta, yaml.safe_dump(payload, sort_keys=False)
