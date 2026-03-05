"""Task persistence helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
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
            "inputs",
        ]:
            (folder / part).mkdir(parents=True, exist_ok=True)
        manifest = folder / "inputs" / "attachments.json"
        if not manifest.exists():
            manifest.write_text("[]", encoding="utf-8")
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

    def list_attachments(self, task_id: str) -> list[dict[str, object]]:
        """Load registered attachment metadata."""
        manifest = self.task_dir(task_id) / "inputs" / "attachments.json"
        if not manifest.exists():
            return []
        return json.loads(manifest.read_text(encoding="utf-8"))

    def register_attachment(self, task_id: str, source_path: Path, notes: str = "") -> dict[str, object]:
        """Copy and register attachment metadata."""
        task_inputs = self.task_dir(task_id) / "inputs"
        task_inputs.mkdir(parents=True, exist_ok=True)
        target = task_inputs / source_path.name
        target.write_bytes(source_path.read_bytes())
        row = {
            "path": str(target.relative_to(self.task_dir(task_id))),
            "filename": target.name,
            "type": target.suffix.lower().lstrip("."),
            "size_bytes": target.stat().st_size,
            "sha256": _hash_file(target),
            "added_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes,
        }
        manifest = task_inputs / "attachments.json"
        items = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
        items.append(row)
        manifest.write_text(json.dumps(items, indent=2), encoding="utf-8")
        return row


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
