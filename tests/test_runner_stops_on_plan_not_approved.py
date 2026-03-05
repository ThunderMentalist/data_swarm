from pathlib import Path

from data_swarm.orchestrator.runner import run_task
from data_swarm.orchestrator.task_models import Task
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_runner_stops_when_planner_not_approved(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    for part in ["tasks", "memory", "indexes", "logs", "kb"]:
        (home / part).mkdir(parents=True, exist_ok=True)
    (home / "tone_profile.md").write_text("tone", encoding="utf-8")
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")

    store = TaskStore(home)
    task = Task(task_id="r1", title="Runner", description="desc")
    task_dir = store.create(task)
    (task_dir / "01_triage" / "final_brief.json").write_text("{}", encoding="utf-8")

    io = FakeIO(answers=["n", "deadline", "END", "success", "END", "risk", "END", "dep", "END", "n"])
    run_task(task.task_id, config={}, home=home, io=io)

    assert not (task_dir / "03_stakeholders" / "03_stakeholders.yaml").exists()
    assert not (task_dir / "04_navigation" / "04_navigation.md").exists()
    assert not (task_dir / "05_comms" / "final_comms.json").exists()
