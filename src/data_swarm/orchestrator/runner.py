"""Pipeline runner."""

from __future__ import annotations

from pathlib import Path

from data_swarm.agents.deliverable import run_deliverable
from data_swarm.kb import load_kb
from data_swarm.orchestrator.run_mode import policy_for_mode, resolve_run_mode
from data_swarm.orchestrator.task_models import TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.comms.stage import CommsStage
from data_swarm.stages.intake_refine.stage import IntakeRefineStage
from data_swarm.stages.navigation.stage import NavigationStage
from data_swarm.stages.planner.stage import PlannerStage
from data_swarm.stages.reaction.stage import ReactionStage
from data_swarm.stages.stakeholder.stage import StakeholderStage
from data_swarm.stages.triage.stage import TriageStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.memory_store import MemoryStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import ConsoleIO, UserIO


def _event(logs: LogStore, task_id: str, stage: str, event_type: str, message: str, data: dict | None = None) -> None:
    logs.event(task_id, stage, event_type, message, data or {})


def run_task(task_id: str, config: dict, home: Path, io: UserIO | None = None, run_mode_override: str = "") -> None:
    io = io or ConsoleIO()
    store = TaskStore(home)
    task = store.load(task_id)
    mode = resolve_run_mode(run_mode_override or task.run_mode or config.get("run_mode", "INITIAL_USING"))
    task.run_mode = mode.value
    task.is_demo = mode.value == "DEMO"
    store.save(task)
    policy = policy_for_mode(mode)

    task_dir = store.task_dir(task_id)
    anonymizer = Anonymizer(home / "kb" / "personas.yaml")
    logs = LogStore(task_dir, anonymizer=anonymizer, strict_redaction=policy.strict_redaction)
    kb = load_kb(home)
    memory_store = MemoryStore(home)

    stages: list[tuple[str, object]] = []
    if task.state == TaskState.AWAITING_REPLIES:
        stages.append(("reaction", ReactionStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)))
    stages.extend([
        ("intake_refine", IntakeRefineStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("triage", TriageStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("planner", PlannerStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("stakeholder", StakeholderStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("navigation", NavigationStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
        ("comms", CommsStage(config=config, home=home, io=io, store=store, logs=logs, anonymizer=anonymizer)),
    ])

    attachments = store.list_attachments(task_id)
    for stage_name, stage in stages:
        task = store.load(task_id)
        if stage_name == "reaction" and task.state == TaskState.AWAITING_REPLIES:
            pass
        _event(logs, task_id, stage_name, "stage_start", f"{stage_name} started")
        result = stage.run(task, task_dir, kb, attachments)
        _event(logs, task_id, stage_name, "stage_complete", f"{stage_name} finished", {"approved": result.approved, "skipped": result.skipped, "state_after": result.state_after.value, "artifacts_written": result.artifacts_written})
        if stage_name == "reaction" and result.approved and task.state != TaskState.REPLANNING:
            apply_transition(task, TaskState.REPLANNING, "reaction approved", result.artifacts_written, store, logs, "reaction")
            task.cycle_id += 1
            store.save(task)
        if not result.approved:
            logs.run_log(f"pipeline stopped: {stage_name} not approved")
            if policy.allow_persona_learning:
                anonymizer.write_kb_proposal(task_dir)
            return
        task = store.load(task_id)
        if task.state == TaskState.AWAITING_REPLIES:
            logs.run_log("Pipeline paused at AWAITING_REPLIES. Re-run after replies using reaction stage.")
            return

    if store.load(task_id).state != TaskState.READY_TO_DELIVER:
        return

    merged_config = dict(config)
    merged_config["data_swarm_home"] = str(home)
    run_deliverable(task, task_dir, merged_config, io=io)

    apply_transition(task, TaskState.DELIVERED, "deliverable stage complete", ["07_deliverable/summary.md"], store, logs, "deliverable")
    if policy.allow_persona_learning:
        anonymizer.write_kb_proposal(task_dir)
    if policy.allow_kb_apply_prompt:
        anonymizer.apply_proposal(io)
    logs.run_log("pipeline completed")
