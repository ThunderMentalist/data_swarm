"""Comms curator agent."""

from __future__ import annotations

from data_swarm import yaml_compat as yaml
from data_swarm.stages.policy_store import PolicyPack


class CommsCuratorAgent:
    name = "Comms Curator Agent"

    def curate(self, initial_drafts: dict, final_comms: dict, policy: PolicyPack) -> tuple[str, str]:
        changed = len(final_comms.get("channels", []))
        delta = "\n".join(["# Comms Delta Learning", "", f"- Channels changed: {changed}", f"- Policy cards considered: {len(policy.behaviour_cards)}"]) + "\n"
        payload = {"facts": ["Approved comms were captured for outreach."], "behaviour_cards": [{"title": "Require per-channel approval copy", "guidance": "Collect explicit approved text for each channel.", "evidence": str(final_comms)[:180]}]}
        return delta, yaml.safe_dump(payload, sort_keys=False)
