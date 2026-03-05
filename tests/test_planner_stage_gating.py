from pathlib import Path

from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.planner.stage import PlannerStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_planner_stage_requires_approval(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    home.mkdir()
    store = TaskStore(home)
    task = Task(task_id="p1", title="Plan it", description="desc")
    task_dir = store.create(task)
    io = FakeIO(answers=["deadline", "END", "success", "END", "risk", "END", "dep", "END", "n"])

    result = PlannerStage(config={}, home=home, io=io, store=store, logs=LogStore(task_dir)).run(task, task_dir)

    plan_dir = task_dir / "02_plan"
    assert (plan_dir / "initial_plan.md").exists()
    assert (plan_dir / "draft_plan.md").exists()
    assert not (plan_dir / "02_plan.md").exists()
    assert (plan_dir / "iterations.jsonl").exists()
    assert result.approved is False
