"""Triage curator agent."""

from __future__ import annotations

from data_swarm import yaml_compat as yaml
from data_swarm.stages.triage.models import TaskBrief


class TriageCuratorAgent:
    """Triage Curator Agent."""

    name = "Triage Curator Agent"

    def curate(self, initial_brief: TaskBrief, final_brief: TaskBrief) -> tuple[str, str]:
        """Return delta-learning markdown and YAML learning candidates."""
        fields = [
            "goal",
            "deliverable",
            "audience",
            "context",
            "deadline",
            "constraints",
            "inputs_available",
            "success_criteria",
            "unknowns",
            "assumptions",
            "risks",
        ]
        diffs: list[str] = []
        facts: list[str] = []
        for field in fields:
            before = getattr(initial_brief, field)
            after = getattr(final_brief, field)
            if before != after:
                diffs.append(f"- **{field}** changed from `{before}` to `{after}`")
                facts.append(f"{field} refinement improved planning readiness")

        delta_md = "\n".join(
            [
                "# Triage Delta Learning",
                "",
                "This summary captures improvements between initial and approved brief.",
                "",
                "## Field-level diff",
                *(diffs or ["- No differences captured."]),
            ]
        )

        payload = {
            "facts": facts or ["Approved brief confirms baseline intake expectations."],
            "behaviour_cards": [
                {
                    "title": "Ask for measurable outcomes before planning",
                    "guidance": "Capture explicit acceptance criteria during triage.",
                    "evidence": "Approved briefs with measurable criteria reduce replanning.",
                }
            ],
        }
        return delta_md, yaml.safe_dump(payload, sort_keys=False)
