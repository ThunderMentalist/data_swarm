from pathlib import Path

from data_swarm.orchestrator.runner import run_task
from data_swarm.orchestrator.task_models import Task
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def _setup_home(tmp_path: Path) -> Path:
    home = tmp_path / ".data_swarm"
    for part in ["tasks", "memory", "indexes", "logs", "kb"]:
        (home / part).mkdir(parents=True, exist_ok=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    return home


def test_triage_stage_approval_generates_outputs_and_continues(tmp_path: Path) -> None:
    home = _setup_home(tmp_path)
    store = TaskStore(home)
    task = Task(task_id="t2", title="Task", description="Need a plan", task_type="general")
    store.create(task)

    answers = [
        "intake note", "END", "1",
        "Goal text", "END", "Deliverable text", "END", "Audience text", "END", "Deadline text", "END",
        "Success 1", "END", "Constraints 1", "END", "Inputs 1", "END", "1",
        "deadline", "END", "success", "END", "risk", "END", "deps", "END", "4",
    ]
    io = FakeIO(answers=answers)

    run_task(task.task_id, config={}, home=home, io=io)

    triage_dir = home / "tasks" / task.task_id / "01_triage" / "cycle_0001"
    assert (triage_dir / "final_brief.json").exists()
    assert (home / "tasks" / task.task_id / "06_reaction" / "triage_update_patch.json").exists() is False
