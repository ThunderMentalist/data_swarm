"""Comms curator agent."""

from __future__ import annotations

import re

from data_swarm import yaml_compat as yaml


class CommsCuratorAgent:
    """Comms Curator Agent."""

    name = "Comms Curator Agent"

    def curate(self, initial_drafts: dict[str, str], final_comms: dict[str, str]) -> tuple[str, str]:
        """Create comms delta and learning candidates."""
        changed = [channel for channel, content in final_comms.items() if content != initial_drafts.get(channel, "")]
        delta = "\n".join([
            "# Comms Delta Learning",
            "",
            f"- Channels changed: {', '.join(changed) if changed else 'none'}",
            f"- Total channels: {len(final_comms)}",
        ]) + "\n"
        evidence = re.sub(r"[\w.+-]+@[\w.-]+", "[REDACTED_EMAIL]", "\n".join(final_comms.values()))
        payload = {
            "facts": ["Approved comms were captured for outreach."],
            "behaviour_cards": [
                {
                    "title": "Require per-channel approval copy",
                    "guidance": "Collect explicit approved text for each communication channel.",
                    "evidence": evidence[:180],
                }
            ],
        }
        return delta, yaml.safe_dump(payload, sort_keys=False)
