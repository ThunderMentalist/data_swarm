"""Triage concierge agent."""

from __future__ import annotations

import json

from data_swarm.stages.triage.models import TaskBrief
from data_swarm.stages.triage.policy import TriagePolicyPack
from data_swarm.tools.redaction import redact_identifiers


class TriageConciergeAgent:
    """Triage Concierge Agent."""

    name = "Triage Concierge Agent"

    def __init__(self, policy_pack: TriagePolicyPack) -> None:
        self.policy_pack = policy_pack

    def propose_initial_brief(self, intake_text: str) -> TaskBrief:
        """Create an initial brief from intake content."""
        brief = TaskBrief.empty()
        brief.context = redact_identifiers(intake_text).strip()
        return brief

    def next_questions(self, brief: TaskBrief) -> list[str]:
        """Return next batch of clarifying questions."""
        questions: list[str] = []
        checks = [
            ("goal", brief.goal, "What is the primary goal for this task?"),
            ("deliverable", brief.deliverable, "What exact deliverable is expected?"),
            ("audience", brief.audience, "Who is the target audience or stakeholder group?"),
            ("deadline", brief.deadline, "What is the deadline or required timeline?"),
            ("success", bool(brief.success_criteria), "What are the success criteria?"),
            ("constraints", bool(brief.constraints), "What constraints should be respected?"),
            ("inputs", bool(brief.inputs_available), "What inputs or data are already available?"),
            ("risks", bool(brief.risks), "What risks or blockers do you foresee?"),
        ]
        for _, present, question in checks:
            if present:
                continue
            questions.append(question)
            if len(questions) >= 7:
                break
        if len(questions) < 3:
            questions.extend(
                [
                    "Any unknowns we should capture before planning begins?",
                    "Any assumptions we should explicitly document?",
                    "Any additional context or notes to preserve?",
                ][: 3 - len(questions)]
            )
        return questions

    def apply_answers(self, brief: TaskBrief, qa: list[tuple[str, str]]) -> TaskBrief:
        """Apply Q/A responses onto the structured brief."""
        updated = TaskBrief.from_dict(brief.to_dict())
        for question, answer in qa:
            cleaned = answer.strip()
            lowered = question.lower()
            if not cleaned:
                continue
            if "goal" in lowered:
                updated.goal = cleaned
            elif "deliverable" in lowered:
                updated.deliverable = cleaned
            elif "audience" in lowered:
                updated.audience = cleaned
            elif "deadline" in lowered or "timeline" in lowered:
                updated.deadline = cleaned
            elif "success" in lowered:
                updated.success_criteria.extend(_split_lines(cleaned))
            elif "constraints" in lowered:
                updated.constraints.extend(_split_lines(cleaned))
            elif "inputs" in lowered or "data" in lowered:
                updated.inputs_available.extend(_split_lines(cleaned))
            elif "risks" in lowered or "blockers" in lowered:
                updated.risks.extend(_split_lines(cleaned))
            elif "unknowns" in lowered:
                updated.unknowns.extend(_split_lines(cleaned))
            elif "assumptions" in lowered:
                updated.assumptions.extend(_split_lines(cleaned))
            else:
                note = f"Notes: {cleaned}"
                updated.context = f"{updated.context}\n{note}".strip()
        return updated

    @staticmethod
    def format_brief(brief: TaskBrief) -> str:
        """Return pretty JSON format for display."""
        return json.dumps(brief.to_dict(), indent=2)


def _split_lines(text: str) -> list[str]:
    return [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
