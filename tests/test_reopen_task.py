from pathlib import Path

from data_swarm.orchestrator.reopen import reopen_task
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore


def test_reopen_closed_task_increments_cycle(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    (home / "tasks").mkdir(parents=True)
    store = TaskStore(home)
    task = Task(task_id="x1", title="t", description="d", state=TaskState.CLOSED, cycle_id=1)
    task_dir = store.create(task)
    reopen_task(task.task_id, store, LogStore(task_dir))
    updated = store.load(task.task_id)
    assert updated.state == TaskState.REPLANNING
    assert updated.cycle_id == 2
