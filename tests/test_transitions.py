import json
from pathlib import Path

from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore


def test_apply_transition_persists_and_logs(tmp_path: Path) -> None:
    store = TaskStore(tmp_path)
    task = Task(task_id="t1", title="x", description="y")
    store.create(task)
    logs = LogStore(store.task_dir("t1"))

    apply_transition(task, TaskState.PLANNED, "planning complete", ["02_plan/02_plan.md"], store, logs, "planner")

    loaded = store.load("t1")
    assert loaded.state == TaskState.PLANNED

    events = (store.task_dir("t1") / "08_logs" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    payload = json.loads(events[0])
    assert payload["event_type"] == "state_transition"
    assert payload["data"]["from_state"] == "NEW"
    assert payload["data"]["to_state"] == "PLANNED"
    assert payload["data"]["reason"] == "planning complete"
