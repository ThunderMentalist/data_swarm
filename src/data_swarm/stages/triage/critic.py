"""Triage critic agent."""

from __future__ import annotations

from data_swarm.stages.triage.models import TaskBrief


class TriageCriticAgent:
    """Triage Critic Agent."""

    name = "Triage Critic Agent"

    def evaluate(
        self,
        initial_brief: TaskBrief,
        final_brief: TaskBrief,
        clarification_log_tail: list[dict[str, str]],
    ) -> dict[str, list]:
        """Evaluate triage quality and provide actionable suggestions."""
        strengths: list[str] = []
        gaps: list[str] = []
        if final_brief.goal:
            strengths.append("Clear goal captured.")
        if final_brief.deliverable:
            strengths.append("Deliverable is defined.")
        if not final_brief.success_criteria:
            gaps.append("Success criteria need more measurable detail.")
        if not final_brief.constraints:
            gaps.append("Constraints are underspecified.")
        suggestion = {
            "title": "Strengthen measurable acceptance criteria",
            "rationale": "Explicit metrics reduce downstream ambiguity.",
            "evidence": f"Clarification entries reviewed: {len(clarification_log_tail)}",
        }
        return {
            "strengths": strengths or ["Brief approved with core fields populated."],
            "gaps": gaps or ["No major structural gaps detected."],
            "suggestions": [suggestion],
        }
