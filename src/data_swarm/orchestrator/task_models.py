"""Task models and enums."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    """Task lifecycle state."""

    NEW = "NEW"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    TRIAGED = "TRIAGED"
    PLANNED = "PLANNED"
    OUTREACH_PENDING_REVIEW = "OUTREACH_PENDING_REVIEW"
    AWAITING_REPLIES = "AWAITING_REPLIES"
    REPLANNING = "REPLANNING"
    BLOCKED = "BLOCKED"
    READY_TO_DELIVER = "READY_TO_DELIVER"
    DELIVERED = "DELIVERED"
    CLOSED = "CLOSED"


@dataclass
class Task:
    """Strict task schema."""

    task_id: str
    title: str
    description: str
    task_type: str = "general"
    desired_outcome: str = ""
    deadline: str | None = None
    urgency: str = "medium"
    impact: str = "medium"
    sensitivity: str = "internal"
    clarifying_questions: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    state: TaskState = TaskState.NEW
    run_mode: str = ""
    is_demo: bool = False
    cycle_id: int = 1
    raw_input_path: str = "00_intake/raw_input.md"
    refined_task_path: str = "00_intake/refined_task.md"
    refined_context_path: str = "00_intake/context.yaml"
    attachments_summary_path: str = "00_intake/attachments_summary.md"
    refined_task_digest: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize task object."""
        payload = asdict(self)
        payload["state"] = self.state.value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Task:
        """Deserialize task object."""
        data = dict(payload)
        data["state"] = TaskState(data.get("state", TaskState.NEW.value))
        data.setdefault("run_mode", "")
        data.setdefault("is_demo", False)
        data.setdefault("cycle_id", 1)
        data.setdefault("raw_input_path", "00_intake/raw_input.md")
        data.setdefault("refined_task_path", "00_intake/refined_task.md")
        data.setdefault("refined_context_path", "00_intake/context.yaml")
        data.setdefault("attachments_summary_path", "00_intake/attachments_summary.md")
        data.setdefault("refined_task_digest", "")
        return cls(**data)
