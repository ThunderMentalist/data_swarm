from pathlib import Path

from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.navigation.stage import NavigationStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_navigation_stage_requires_approval(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    home.mkdir()
    store = TaskStore(home)
    task = Task(task_id="n1", title="Nav", description="desc")
    task_dir = store.create(task)
    io = FakeIO(answers=["first", "END", "seq", "END", "risk", "END", "", "END", "n"])

    result = NavigationStage(config={}, home=home, io=io, store=store, logs=LogStore(task_dir)).run(task, task_dir)

    stage_dir = task_dir / "04_navigation"
    assert (stage_dir / "initial_navigation.md").exists()
    assert (stage_dir / "navigation_history.jsonl").exists()
    assert not (stage_dir / "04_navigation.md").exists()
    assert result.approved is False
