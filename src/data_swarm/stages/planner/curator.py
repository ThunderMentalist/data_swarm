"""Planner curator agent."""

from __future__ import annotations

import re

from data_swarm import yaml_compat as yaml


class PlannerCuratorAgent:
    """Planner Curator Agent."""

    name = "Planner Curator Agent"

    def curate(self, initial_plan: str, final_plan: str) -> tuple[str, str]:
        """Produce delta markdown and learning candidates YAML."""
        delta = "\n".join(
            [
                "# Planner Delta Learning",
                "",
                "## Text diff summary",
                f"- Initial length: {len(initial_plan)}",
                f"- Final length: {len(final_plan)}",
                "- Final plan includes additional HITL guidance." if final_plan != initial_plan else "- No textual differences.",
            ]
        ) + "\n"
        redacted = re.sub(r"[\w.+-]+@[\w.-]+", "[REDACTED_EMAIL]", final_plan)
        payload = {
            "facts": ["Human clarifications improved planning specificity."],
            "behaviour_cards": [
                {
                    "title": "Capture explicit success criteria in planning",
                    "guidance": "Ask and record measurable outcomes before execution.",
                    "evidence": redacted[:180],
                }
            ],
        }
        return delta, yaml.safe_dump(payload, sort_keys=False)
