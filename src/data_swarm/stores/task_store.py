"""Task persistence helpers."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm.orchestrator.task_models import Task


class TaskStore:
    """File-based task store under DATA_SWARM_HOME/tasks."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def task_dir(self, task_id: str) -> Path:
        """Return task directory path."""
        return self.root / "tasks" / task_id

    def create(self, task: Task) -> Path:
        """Create task artifact directories and initial payload."""
        folder = self.task_dir(task.task_id)
        for part in [
            "00_intake",
            "01_triage",
            "02_plan",
            "03_stakeholders",
            "04_navigation",
            "05_comms",
            "06_feedback",
            "07_deliverable",
            "08_logs",
        ]:
            (folder / part).mkdir(parents=True, exist_ok=True)
        self.save(task)
        return folder

    def save(self, task: Task) -> None:
        """Persist task JSON."""
        path = self.task_dir(task.task_id) / "task.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(task.to_dict(), indent=2), encoding="utf-8")

    def load(self, task_id: str) -> Task:
        """Load task JSON."""
        path = self.task_dir(task_id) / "task.json"
        return Task.from_dict(json.loads(path.read_text(encoding="utf-8")))
