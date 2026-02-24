"""Deliverable router."""

from __future__ import annotations

from pathlib import Path

from data_swarm.orchestrator.task_models import Task
from data_swarm.projects.meridian_aux.project import MeridianAuxProject
from data_swarm.tools.io import UserIO


def run_deliverable(task: Task, task_dir: Path, config: dict, io: UserIO) -> None:
    """Route deliverable execution by task type."""
    if task.task_type == "meridian_aux_codegen":
        MeridianAuxProject(config, io=io).run(task, task_dir)
    else:
        out = task_dir / "07_deliverable" / "notes.md"
        out.write_text("Deliverable plugin not implemented for this task_type.\n", encoding="utf-8")
        (task_dir / "07_deliverable" / "summary.md").write_text("No plugin execution performed.\n", encoding="utf-8")
