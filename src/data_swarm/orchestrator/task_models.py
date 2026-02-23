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
    confidence: float = 0.0
    clarifying_questions: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    state: TaskState = TaskState.NEW
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
        return cls(**data)
