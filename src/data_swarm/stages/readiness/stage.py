"""Readiness evaluator stage."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.artifacts import load_stage_inputs
from data_swarm.stages.reaction.models import ReadinessDecision


class ReadinessStage:
    name = "readiness"

    def __init__(self, config: dict):
        self.config = config

    def evaluate(self, task: Task, task_dir: Path) -> ReadinessDecision:
        upstream = load_stage_inputs(task_dir)
        reaction = upstream.get("reaction", {})
        recommended = reaction.get("readiness_recommendation", "AWAITING_REPLIES")
        blockers = reaction.get("blockers", [])
        if blockers and recommended == "READY_TO_DELIVER":
            recommended = "REPLANNING"
        if recommended not in {"AWAITING_REPLIES", "REPLANNING", "READY_TO_DELIVER"}:
            recommended = "AWAITING_REPLIES"
        rationale = reaction.get("readiness_reason", "Awaiting operator review.")
        decision = ReadinessDecision(recommended_state=recommended, rationale=rationale, requires_operator_approval=True)
        out = task_dir / "06_reaction" / "readiness_recommendation.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(decision.to_dict(), indent=2), encoding="utf-8")
        return decision

    @staticmethod
    def to_task_state(value: str) -> TaskState | None:
        mapping = {
            "REPLANNING": TaskState.REPLANNING,
            "READY_TO_DELIVER": TaskState.READY_TO_DELIVER,
            "AWAITING_REPLIES": TaskState.AWAITING_REPLIES,
        }
        return mapping.get(value)
