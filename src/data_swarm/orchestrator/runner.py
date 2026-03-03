"""Pipeline runner."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm.agents.deliverable import run_deliverable
from data_swarm.agents.feedback import FeedbackAgent
from data_swarm.orchestrator.task_models import TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.comms.stage import CommsStage
from data_swarm.stages.navigation.stage import NavigationStage
from data_swarm.stages.planner.stage import PlannerStage
from data_swarm.stages.stakeholder.stage import StakeholderStage
from data_swarm.stages.triage.stage import TriageStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.memory_store import MemoryStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import ConsoleIO, UserIO
from data_swarm.tools.redaction import sanitize_feedback


def _event(logs: LogStore, task_id: str, stage: str, event_type: str, message: str, data: dict | None = None) -> None:
    logs.event(task_id, stage, event_type, message, data or {})


def run_task(task_id: str, config: dict, home: Path, io: UserIO | None = None) -> None:
    """Run task pipeline with explicit HITL prompts."""
    io = io or ConsoleIO()
    store = TaskStore(home)
    task = store.load(task_id)
    task_dir = store.task_dir(task_id)
    logs = LogStore(task_dir)
    memory = MemoryStore(home)

    intake_path = task_dir / "00_intake" / "00_intake.md"
    if not intake_path.exists():
        sanitized_intake, _ = sanitize_feedback(task.description, io)
        intake_path.write_text(sanitized_intake, encoding="utf-8")

    stages = [
        ("triage", TriageStage(config=config, home=home, io=io, store=store, logs=logs)),
        ("planner", PlannerStage(config=config, home=home, io=io, store=store, logs=logs)),
        ("stakeholder", StakeholderStage(config=config, home=home, io=io, store=store, logs=logs)),
        ("navigation", NavigationStage(config=config, home=home, io=io, store=store, logs=logs)),
        ("comms", CommsStage(config=config, home=home, io=io, store=store, logs=logs)),
    ]

    for stage_name, stage in stages:
        _event(logs, task_id, stage_name, "stage_start", f"{stage_name} started")
        result = stage.run(task, task_dir)
        _event(logs, task_id, stage_name, "stage_complete", f"{stage_name} finished", {"approved": result.approved})
        if not result.approved:
            logs.run_log(f"pipeline stopped: {stage_name} not approved")
            return

    _event(logs, task_id, "feedback", "stage_start", "feedback started")
    feedback_text = io.ask("Paste reply summary (or blank): ")
    feedback = FeedbackAgent().run(feedback_text, io)
    (task_dir / "06_feedback" / "06_feedback.json").write_text(
        json.dumps(feedback.__dict__, indent=2),
        encoding="utf-8",
    )
    for role in feedback.roles_used:
        memory.add_role_note(role, "Feedback captured for role-level memory", task_id)
    if feedback.facts_learned:
        memory.add_org_playbook("feedback_facts", " | ".join(feedback.facts_learned), task_id)
    _event(logs, task_id, "feedback", "stage_complete", "feedback finished")

    apply_transition(
        task,
        TaskState.READY_TO_DELIVER,
        "ready for deliverable execution",
        ["06_feedback/06_feedback.json"],
        store,
        logs,
        "deliverable",
    )
    merged_config = dict(config)
    merged_config["data_swarm_home"] = str(home)
    run_deliverable(task, task_dir, merged_config, io=io)

    apply_transition(
        task,
        TaskState.DELIVERED,
        "deliverable stage complete",
        ["07_deliverable/summary.md"],
        store,
        logs,
        "deliverable",
    )
    (task_dir / "closeout.md").write_text("Task delivered; close after review.", encoding="utf-8")
    logs.run_log("pipeline completed")
