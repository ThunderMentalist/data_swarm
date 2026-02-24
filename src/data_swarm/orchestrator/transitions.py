"""Helpers for validated and persisted task transitions."""

from __future__ import annotations

from data_swarm.orchestrator.state_machine import transition
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore


def apply_transition(
    task: Task,
    target: TaskState,
    reason: str,
    artifacts: list[str],
    store: TaskStore,
    logs: LogStore,
    stage: str,
) -> None:
    """Validate transition and persist task + transition event."""
    record = transition(task.state, target, reason, artifacts)
    task.state = target
    store.save(task)
    logs.event(
        task.task_id,
        stage,
        "state_transition",
        reason,
        {
            "from_state": record.from_state,
            "to_state": record.to_state,
            "reason": record.reason,
            "timestamp": record.timestamp,
            "artifacts": record.artifacts,
        },
    )
