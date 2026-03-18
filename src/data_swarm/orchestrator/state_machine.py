"""Task state machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from data_swarm.orchestrator.task_models import TaskState

ACTIVE_STATES = {
    TaskState.NEW,
    TaskState.NEEDS_CLARIFICATION,
    TaskState.TRIAGED,
    TaskState.PLANNED,
    TaskState.OUTREACH_PENDING_REVIEW,
    TaskState.AWAITING_REPLIES,
    TaskState.REPLANNING,
    TaskState.READY_TO_DELIVER,
    TaskState.DELIVERED,
}

ALLOWED_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.NEW: {TaskState.NEEDS_CLARIFICATION, TaskState.TRIAGED, TaskState.BLOCKED, TaskState.CLOSED},
    TaskState.NEEDS_CLARIFICATION: {TaskState.TRIAGED, TaskState.BLOCKED, TaskState.CLOSED},
    TaskState.TRIAGED: {TaskState.PLANNED, TaskState.REPLANNING, TaskState.BLOCKED, TaskState.CLOSED},
    TaskState.PLANNED: {TaskState.OUTREACH_PENDING_REVIEW, TaskState.REPLANNING, TaskState.BLOCKED, TaskState.CLOSED},
    TaskState.OUTREACH_PENDING_REVIEW: {TaskState.AWAITING_REPLIES, TaskState.REPLANNING, TaskState.BLOCKED, TaskState.CLOSED},
    TaskState.AWAITING_REPLIES: {TaskState.REPLANNING, TaskState.READY_TO_DELIVER, TaskState.BLOCKED, TaskState.CLOSED},
    TaskState.REPLANNING: {TaskState.OUTREACH_PENDING_REVIEW, TaskState.READY_TO_DELIVER, TaskState.BLOCKED, TaskState.CLOSED},
    TaskState.BLOCKED: {TaskState.REPLANNING, TaskState.CLOSED},
    TaskState.READY_TO_DELIVER: {TaskState.DELIVERED, TaskState.BLOCKED, TaskState.CLOSED},
    TaskState.DELIVERED: {TaskState.CLOSED, TaskState.REPLANNING, TaskState.BLOCKED},
    TaskState.CLOSED: {TaskState.REPLANNING},
}


@dataclass
class TransitionRecord:
    from_state: str
    to_state: str
    reason: str
    timestamp: str
    artifacts: list[str]


class InvalidTransitionError(ValueError):
    """Raised when transition is invalid."""


def transition(current: TaskState, target: TaskState, reason: str, artifacts: list[str]) -> TransitionRecord:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransitionError(f"Cannot move from {current.value} to {target.value}")
    return TransitionRecord(
        from_state=current.value,
        to_state=target.value,
        reason=reason,
        timestamp=datetime.now(timezone.utc).isoformat(),
        artifacts=artifacts,
    )
