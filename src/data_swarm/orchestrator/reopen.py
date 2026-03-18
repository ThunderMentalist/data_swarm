"""Task reopen helper."""

from __future__ import annotations

from data_swarm.orchestrator.task_models import TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore


def reopen_task(task_id: str, store: TaskStore, logs: LogStore) -> None:
    task = store.load(task_id)
    apply_transition(task, TaskState.REPLANNING, "task reopened; new cycle", [], store, logs, "operator")
    task.cycle_id += 1
    store.save(task)
