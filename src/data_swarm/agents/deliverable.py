"""Deliverable router."""

from __future__ import annotations

from pathlib import Path

from data_swarm.orchestrator.task_models import Task
from data_swarm.projects.meridian_aux.project import MeridianAuxProject


def run_deliverable(task: Task, task_dir: Path, config: dict) -> None:
    """Route deliverable execution by task type."""
    if task.task_type == "meridian_aux_codegen":
        MeridianAuxProject(config).run(task, task_dir)
    else:
        out = task_dir / "07_deliverable" / "notes.md"
        out.write_text("Deliverable plugin not implemented for this task_type.\n", encoding="utf-8")
