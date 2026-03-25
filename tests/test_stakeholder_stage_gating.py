from pathlib import Path

from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.stakeholder.stage import StakeholderStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_stakeholder_stage_requires_approval(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    home.mkdir()
    store = TaskStore(home)
    task = Task(task_id="s1", title="Map", description="desc")
    task_dir = store.create(task)
    io = FakeIO(answers=["END", "4"])

    result = StakeholderStage(config={}, home=home, io=io, store=store, logs=LogStore(task_dir)).run(task, task_dir)

    stage_dir = task_dir / "03_stakeholders" / "cycle_0001"
    assert (stage_dir / "initial_stakeholders.json").exists()
    assert (stage_dir / "draft_stakeholders.json").exists()
    assert not (stage_dir / "03_stakeholders.json").exists()
    assert (stage_dir / "iterations.jsonl").exists()
    assert result.approved is False
