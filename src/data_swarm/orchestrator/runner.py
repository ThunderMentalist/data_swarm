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
from data_swarm.orchestrator.state_machine import transition
from data_swarm.orchestrator.task_models import TaskState
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.memory_store import MemoryStore
from data_swarm.stores.task_store import TaskStore


def run_task(task_id: str, config: dict, home: Path) -> None:
    """Run task pipeline with HITL prompts."""
    store = TaskStore(home)
    task = store.load(task_id)
    task_dir = store.task_dir(task_id)
    logs = LogStore(task_dir)
    memory = MemoryStore(home)

    triage = TriageAgent().run(task.description)
    (task_dir / "00_intake" / "00_intake.md").write_text(task.description, encoding="utf-8")
    (task_dir / "01_triage" / "01_triage.json").write_text(
        json.dumps({"confidence": triage.confidence, "questions": triage.content.splitlines()}, indent=2),
        encoding="utf-8",
    )
    logs.event(task_id, "triage", "stage_complete", "triage finished", {"confidence": triage.confidence})
    if triage.confidence < 0.6:
        task.state = TaskState.NEEDS_CLARIFICATION
        answers = input(f"Clarify task ({triage.content}): ")
        approve = input("Approve intent to proceed? [y/N]: ").strip().lower()
        (task_dir / "01_triage" / "01_task_brief.md").write_text(answers, encoding="utf-8")
        (task_dir / "01_triage" / "01_approved_intent.json").write_text(
            json.dumps({"approved": approve == "y"}), encoding="utf-8"
        )

    plan = PlannerAgent().run(task.title)
    (task_dir / "02_plan" / "02_plan.md").write_text(plan.content, encoding="utf-8")
    for name in ["assumptions", "unknowns", "dependencies", "next_actions"]:
        (task_dir / "02_plan" / f"{name}.yaml").write_text(
            yaml.safe_dump([{"item": f"{name} placeholder", "owner": "agent"}], sort_keys=False),
            encoding="utf-8",
        )
    transition(task.state, TaskState.PLANNED, "planning complete", ["02_plan/02_plan.md"])
    task.state = TaskState.PLANNED

    (task_dir / "03_stakeholders" / "03_stakeholders.yaml").write_text(
        StakeholderMapAgent().run().content, encoding="utf-8"
    )
    (task_dir / "04_navigation" / "04_navigation.md").write_text(NavigationAgent().run().content, encoding="utf-8")

    comms = CommunicationAgent().run(home / "tone_profile.md", task.description)
    comms_dir = task_dir / "05_comms"
    (comms_dir / "email_draft.md").write_text(comms.content, encoding="utf-8")
    (comms_dir / "teams_draft.md").write_text("Short update: " + task.title, encoding="utf-8")
    (comms_dir / "talking_points.md").write_text("- status\n- risks\n- asks", encoding="utf-8")
    (comms_dir / "meeting_brief.md").write_text("Objective and agenda", encoding="utf-8")
    task.state = TaskState.OUTREACH_PENDING_REVIEW
    final_copy = input("Review comms and paste approved email copy: ")
    (comms_dir / "email_approved.md").write_text(final_copy, encoding="utf-8")
    task.state = TaskState.AWAITING_REPLIES

    feedback_text = input("Paste reply summary (or blank): ")
    feedback = FeedbackAgent().run(feedback_text)
    (task_dir / "06_feedback" / "06_feedback.json").write_text(
        json.dumps({"feedback": feedback.content}, indent=2), encoding="utf-8"
    )
    if feedback.content:
        memory.add_role_note("Client Lead", "Preferred concise updates", task_id)

    task.state = TaskState.READY_TO_DELIVER
    merged_config = dict(config)
    merged_config["data_swarm_home"] = str(home)
    run_deliverable(task, task_dir, merged_config)

    task.state = TaskState.DELIVERED
    (task_dir / "closeout.md").write_text("Task delivered; close after review.", encoding="utf-8")
    store.save(task)
    logs.run_log("pipeline completed")
