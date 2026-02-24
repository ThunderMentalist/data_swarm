"""Pipeline runner."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm import yaml_compat as yaml
from data_swarm.agents.communication import CommunicationAgent
from data_swarm.agents.deliverable import run_deliverable
from data_swarm.agents.feedback import FeedbackAgent
from data_swarm.agents.navigation import NavigationAgent
from data_swarm.agents.planner import PlannerAgent
from data_swarm.agents.stakeholder_map import StakeholderMapAgent
from data_swarm.agents.triage import TriageAgent
from data_swarm.orchestrator.hitl import clarification_loop, comms_review
from data_swarm.orchestrator.task_models import TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.memory_store import MemoryStore
from data_swarm.stores.task_store import TaskStore
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
    memory = MemoryStore(home)

    _event(logs, task_id, "triage", "stage_start", "triage started")
    triage = TriageAgent().run(task.description)
    (task_dir / "00_intake" / "00_intake.md").write_text(task.description, encoding="utf-8")
    triage_questions = [line for line in triage.content.splitlines() if line.strip()]
    (task_dir / "01_triage" / "01_triage.json").write_text(
        json.dumps({"confidence": triage.confidence, "questions": triage_questions}, indent=2),
        encoding="utf-8",
    )
    _event(logs, task_id, "triage", "stage_complete", "triage finished", {"confidence": triage.confidence})

    if triage.confidence < config.get("triage", {}).get("confidence_threshold", 0.6):
        apply_transition(
            task,
            TaskState.NEEDS_CLARIFICATION,
            "triage below confidence threshold",
            ["01_triage/01_triage.json"],
            store,
            logs,
            "triage",
        )
        approved, brief, qa_log = clarification_loop(io, triage_questions)
        (task_dir / "01_triage" / "01_task_brief.md").write_text(brief, encoding="utf-8")
        (task_dir / "01_triage" / "01_approved_intent.json").write_text(
            json.dumps({"approved": approved, "qa_log": qa_log}, indent=2),
            encoding="utf-8",
        )

    _event(logs, task_id, "planner", "stage_start", "planning started")
    plan = PlannerAgent().run(task.title)
    (task_dir / "02_plan" / "02_plan.md").write_text(plan.content, encoding="utf-8")
    for name in ["assumptions", "unknowns", "dependencies", "next_actions"]:
        (task_dir / "02_plan" / f"{name}.yaml").write_text(
            yaml.safe_dump([{"item": f"{name} placeholder", "owner": "agent"}], sort_keys=False),
            encoding="utf-8",
        )
    apply_transition(task, TaskState.PLANNED, "planning complete", ["02_plan/02_plan.md"], store, logs, "planner")
    _event(logs, task_id, "planner", "stage_complete", "planning finished")

    _event(logs, task_id, "stakeholder", "stage_start", "stakeholder mapping started")
    (task_dir / "03_stakeholders" / "03_stakeholders.yaml").write_text(
        StakeholderMapAgent().run().content,
        encoding="utf-8",
    )
    _event(logs, task_id, "stakeholder", "stage_complete", "stakeholder mapping finished")

    _event(logs, task_id, "navigation", "stage_start", "navigation started")
    (task_dir / "04_navigation" / "04_navigation.md").write_text(NavigationAgent().run().content, encoding="utf-8")
    _event(logs, task_id, "navigation", "stage_complete", "navigation finished")

    _event(logs, task_id, "comms", "stage_start", "comms started")
    comms = CommunicationAgent().run(home / "tone_profile.md", task.description)
    comms_dir = task_dir / "05_comms"
    drafts = {
        "email": comms.content,
        "teams": "Short update: " + task.title,
        "talking_points": "- status\n- risks\n- asks",
        "meeting_brief": "Objective and agenda",
    }
    (comms_dir / "review_context.md").write_text(
        "# Review Context\n\nGenerated from planning artifacts and task brief.",
        encoding="utf-8",
    )
    reviewed = comms_review(io, drafts)
    for channel, payload in reviewed.items():
        (comms_dir / f"{channel}_draft.md").write_text(payload["draft"], encoding="utf-8")
        (comms_dir / f"{channel}_approved.md").write_text(payload["approved"], encoding="utf-8")
    apply_transition(
        task,
        TaskState.OUTREACH_PENDING_REVIEW,
        "comms drafts generated and reviewed",
        ["05_comms/review_context.md"],
        store,
        logs,
        "comms",
    )
    apply_transition(
        task,
        TaskState.AWAITING_REPLIES,
        "approved comms ready for outreach",
        ["05_comms/email_approved.md"],
        store,
        logs,
        "comms",
    )
    _event(logs, task_id, "comms", "stage_complete", "comms finished")

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
