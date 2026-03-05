import json
from pathlib import Path

from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.feedback.stage import FeedbackStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_task_store_creates_inputs_and_manifest(tmp_path: Path) -> None:
    store = TaskStore(tmp_path)
    task = Task(task_id="a1", title="t", description="d")
    task_dir = store.create(task)
    assert (task_dir / "inputs").exists()
    assert json.loads((task_dir / "inputs" / "attachments.json").read_text(encoding="utf-8")) == []


def test_feedback_stage_writes_triage_patch(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    (home / "kb").mkdir(parents=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    store = TaskStore(home)
    task = Task(task_id="f1", title="t", description="d")
    task_dir = store.create(task)
    io = FakeIO(answers=["Decision was approved.", "END", "y"])
    stage = FeedbackStage(config={}, home=home, io=io, store=store, logs=LogStore(task_dir))
    result = stage.run(task, task_dir)
    assert result.approved is True
    assert (task_dir / "06_feedback" / "triage_update_patch.json").exists()
