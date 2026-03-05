"""Pipeline runner."""

from __future__ import annotations

from pathlib import Path

from data_swarm.agents.deliverable import run_deliverable
from data_swarm.kb import load_kb
from data_swarm.orchestrator.hitl import ask_yes_no
from data_swarm.orchestrator.task_models import TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.comms.stage import CommsStage
from data_swarm.stages.feedback.stage import FeedbackStage
from data_swarm.stages.navigation.stage import NavigationStage
from data_swarm.stages.planner.stage import PlannerStage
from data_swarm.stages.stakeholder.stage import StakeholderStage
from data_swarm.stages.triage.stage import TriageStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import ConsoleIO, UserIO


def _event(logs: LogStore, task_id: str, stage: str, event_type: str, message: str, data: dict | None = None) -> None:
    logs.event(task_id, stage, event_type, message, data or {})


def run_task(task_id: str, config: dict, home: Path, io: UserIO | None = None) -> None:
    """Run task pipeline with explicit HITL prompts."""
    io = io or ConsoleIO()
    store = TaskStore(home)
    task = store.load(task_id)
    task_dir = store.task_dir(task_id)
    logs = LogStore(task_dir)
    kb = load_kb(home)
    anonymizer = Anonymizer(home / "kb" / "personas.yaml")

    intake_path = task_dir / "00_intake" / "00_intake.md"
    if not intake_path.exists():
        intake_path.write_text(anonymizer.collect_from_text(task.description, io)[0], encoding="utf-8")

    stages = [
        ("triage", TriageStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("planner", PlannerStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("stakeholder", StakeholderStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("navigation", NavigationStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("comms", CommsStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("feedback", FeedbackStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
    ]

    attachments = store.list_attachments(task_id)
    for stage_name, stage in stages:
        _event(logs, task_id, stage_name, "stage_start", f"{stage_name} started")
        result = stage.run(task, task_dir, kb, attachments)
        _event(logs, task_id, stage_name, "stage_complete", f"{stage_name} finished", {
            "approved": result.approved,
            "state_after": result.state_after.value,
            "artifacts_written": result.artifacts_written,
        })
        if not result.approved:
            logs.run_log(f"pipeline stopped: {stage_name} not approved")
            anonymizer.write_kb_proposal(task_dir)
            return

    if task.state != TaskState.READY_TO_DELIVER:
        apply_transition(task, TaskState.READY_TO_DELIVER, "ready for deliverable execution", ["06_feedback/final_feedback.json"], store, logs, "deliverable")

    merged_config = dict(config)
    merged_config["data_swarm_home"] = str(home)
    run_deliverable(task, task_dir, merged_config, io=io)

    apply_transition(task, TaskState.DELIVERED, "deliverable stage complete", ["07_deliverable/summary.md"], store, logs, "deliverable")
    if ask_yes_no(io, "Close task now?", default_no=True):
        apply_transition(task, TaskState.CLOSED, "task closed by operator", ["closeout.md"], store, logs, "deliverable")
        (task_dir / "closeout.md").write_text("Task delivered and closed.", encoding="utf-8")
    else:
        (task_dir / "closeout.md").write_text("Task delivered; awaiting manual close.", encoding="utf-8")

    anonymizer.write_kb_proposal(task_dir)
    anonymizer.apply_proposal(io)
    logs.run_log("pipeline completed")
