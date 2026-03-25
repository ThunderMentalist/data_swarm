"""Triage concierge agent."""

from __future__ import annotations

import json

from data_swarm.stages.policy_store import PolicyPack
from data_swarm.stages.triage.models import TaskBrief
from data_swarm.tools.redaction import redact_identifiers


class TriageConciergeAgent:
    name = "Triage Concierge Agent"

    def __init__(self, policy_pack: PolicyPack) -> None:
        self.policy_pack = policy_pack

    def propose_initial_brief(self, intake_text: str) -> TaskBrief:
        brief = TaskBrief.empty()
        brief.context = redact_identifiers(intake_text).strip()
        if "task_type:" in self.policy_pack.core_prompt:
            brief.task_type = self.policy_pack.core_prompt.split("task_type:", 1)[1].splitlines()[0].strip() or "general"
        return brief

    def next_questions(self, brief: TaskBrief) -> list[str]:
        questions: list[str] = []
        checks = [
            ("goal", brief.goal, "What is the primary goal for this task?"),
            ("deliverable", brief.deliverable, "What exact deliverable is expected?"),
            ("audience", brief.audience, "Who is the target audience or stakeholder group?"),
            ("success", bool(brief.success_criteria), "What are the success criteria?"),
            ("constraints", bool(brief.constraints), "What constraints should be respected?"),
            ("inputs", bool(brief.inputs_available), "What inputs or data are already available?"),
            ("attachments", bool(brief.requested_attachments), "Which attachment filenames should be extracted now?"),
        ]
        for _, present, question in checks:
            if not present:
                questions.append(question)
        if not self.policy_pack.core_prompt.strip():
            questions.append("Any policy exceptions the operator wants to document?")
        return questions[:7]

    def apply_answers(self, brief: TaskBrief, qa: list[tuple[str, str]]) -> TaskBrief:
        updated = TaskBrief.from_dict(brief.to_dict())
        for question, answer in qa:
            cleaned = answer.strip()
            if not cleaned:
                continue
            lowered = question.lower()
            if "goal" in lowered:
                updated.goal = cleaned
            elif "deliverable" in lowered:
                updated.deliverable = cleaned
            elif "audience" in lowered:
                updated.audience = cleaned
            elif "success" in lowered:
                updated.success_criteria.extend(_split_lines(cleaned))
            elif "constraints" in lowered:
                updated.constraints.extend(_split_lines(cleaned))
            elif "inputs" in lowered:
                updated.inputs_available.extend(_split_lines(cleaned))
            elif "attachment" in lowered:
                updated.requested_attachments.extend([item.strip() for item in cleaned.split(",") if item.strip()])
            else:
                updated.context = f"{updated.context}\nNotes: {cleaned}".strip()
        return updated

    @staticmethod
    def format_brief(brief: TaskBrief) -> str:
        return json.dumps(brief.to_dict(), indent=2)


def _split_lines(text: str) -> list[str]:
    return [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
