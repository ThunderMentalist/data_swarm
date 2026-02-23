"""Task state machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from data_swarm.orchestrator.task_models import TaskState

ALLOWED_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.NEW: {TaskState.NEEDS_CLARIFICATION, TaskState.PLANNED},
    TaskState.NEEDS_CLARIFICATION: {TaskState.PLANNED, TaskState.BLOCKED},
    TaskState.PLANNED: {TaskState.OUTREACH_PENDING_REVIEW, TaskState.REPLANNING},
    TaskState.OUTREACH_PENDING_REVIEW: {TaskState.AWAITING_REPLIES, TaskState.REPLANNING},
    TaskState.AWAITING_REPLIES: {TaskState.REPLANNING, TaskState.READY_TO_DELIVER},
    TaskState.REPLANNING: {TaskState.OUTREACH_PENDING_REVIEW, TaskState.READY_TO_DELIVER, TaskState.BLOCKED},
    TaskState.BLOCKED: {TaskState.REPLANNING, TaskState.CLOSED},
    TaskState.READY_TO_DELIVER: {TaskState.DELIVERED, TaskState.BLOCKED},
    TaskState.DELIVERED: {TaskState.CLOSED, TaskState.REPLANNING},
    TaskState.CLOSED: set(),
}


@dataclass
class TransitionRecord:
    """State transition log item."""

    from_state: str
    to_state: str
    reason: str
    timestamp: str
    artifacts: list[str]


class InvalidTransitionError(ValueError):
    """Raised when transition is invalid."""


def transition(current: TaskState, target: TaskState, reason: str, artifacts: list[str]) -> TransitionRecord:
    """Validate and return a transition record."""
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransitionError(f"Cannot move from {current.value} to {target.value}")
    return TransitionRecord(
        from_state=current.value,
        to_state=target.value,
        reason=reason,
        timestamp=datetime.now(timezone.utc).isoformat(),
        artifacts=artifacts,
    )
