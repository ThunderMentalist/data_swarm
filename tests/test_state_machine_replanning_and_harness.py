from pathlib import Path

from data_swarm.orchestrator.state_machine import transition
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import FakeIO


def test_replanning_can_transition_to_triaged() -> None:
    record = transition(TaskState.REPLANNING, TaskState.TRIAGED, "retriage", [])
    assert record.to_state == TaskState.TRIAGED.value


def test_invalid_safe_transition_does_not_force_blocked(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    (home / "kb").mkdir(parents=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    store = TaskStore(home)
    task = Task(task_id="x1", title="t", description="d", state=TaskState.NEW)
    task_dir = store.create(task)
    harness = StageHarness(
        StageSpec("test", "00_intake", "i.json", "d.json", "f.json", []),
        io=FakeIO(),
        store=store,
        logs=LogStore(task_dir),
        anonymizer=Anonymizer(home / "kb" / "personas.yaml"),
    )
    ok = harness._safe_transition(task, TaskState.DELIVERED, "bad", [])
    assert ok is False
    assert store.load(task.task_id).state == TaskState.NEW
