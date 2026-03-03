"""Stakeholder curator agent."""

from __future__ import annotations

import re

from data_swarm import yaml_compat as yaml


class StakeholderCuratorAgent:
    """Stakeholder Curator Agent."""

    name = "Stakeholder Curator Agent"

    def curate(self, initial_yaml: str, final_yaml: str) -> tuple[str, str]:
        """Generate stakeholder delta and learning candidates."""
        delta = (
            "# Stakeholder Delta Learning\n\n"
            f"- Initial length: {len(initial_yaml)}\n"
            f"- Final length: {len(final_yaml)}\n"
        )
        redacted = re.sub(r"[\w.+-]+@[\w.-]+", "[REDACTED_EMAIL]", final_yaml)
        payload = {
            "facts": ["Stakeholder mapping improved after review."],
            "behaviour_cards": [
                {
                    "title": "Capture stakeholder influence and cadence",
                    "guidance": "Always include influence plus engagement rhythm.",
                    "evidence": redacted[:180],
                }
            ],
        }
        return delta, yaml.safe_dump(payload, sort_keys=False)
