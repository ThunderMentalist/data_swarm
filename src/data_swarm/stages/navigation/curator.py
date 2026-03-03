"""Navigation curator agent."""

from __future__ import annotations

import re

from data_swarm import yaml_compat as yaml


class NavigationCuratorAgent:
    """Navigation Curator Agent."""

    name = "Navigation Curator Agent"

    def curate(self, initial_doc: str, final_doc: str) -> tuple[str, str]:
        """Generate navigation delta and learning candidates."""
        delta = (
            "# Navigation Delta Learning\n\n"
            f"- Initial length: {len(initial_doc)}\n"
            f"- Final length: {len(final_doc)}\n"
        )
        redacted = re.sub(r"[\w.+-]+@[\w.-]+", "[REDACTED_EMAIL]", final_doc)
        payload = {
            "facts": ["Navigation notes improved sequencing clarity."],
            "behaviour_cards": [
                {
                    "title": "Ask sequencing and risk questions",
                    "guidance": "Capture first-contact order and risk mitigations.",
                    "evidence": redacted[:180],
                }
            ],
        }
        return delta, yaml.safe_dump(payload, sort_keys=False)
