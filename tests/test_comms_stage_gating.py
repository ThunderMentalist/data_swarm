import json
from pathlib import Path

from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.comms.stage import CommsStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_comms_stage_requires_approval(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    home.mkdir()
    (home / "tone_profile.md").write_text("tone", encoding="utf-8")
    store = TaskStore(home)
    task = Task(task_id="c1", title="Comms", description="desc", state=TaskState.PLANNED)
    task_dir = store.create(task)
    io = FakeIO(answers=["", "END", "", "END", "", "END", "", "END", "n"])

    result = CommsStage(config={}, home=home, io=io, store=store, logs=LogStore(task_dir)).run(task, task_dir)

    payload = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    assert payload["state"] == TaskState.REPLANNING.value
    assert not (task_dir / "05_comms" / "final_comms.json").exists()
    assert result.approved is False
