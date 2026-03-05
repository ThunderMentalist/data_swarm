import json
from pathlib import Path

from data_swarm.orchestrator.runner import run_task
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def _setup_home(tmp_path: Path) -> Path:
    home = tmp_path / ".data_swarm"
    for part in ["tasks", "memory", "indexes", "logs", "kb"]:
        (home / part).mkdir(parents=True, exist_ok=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    return home


def test_triage_stage_stops_pipeline_when_not_approved(tmp_path: Path) -> None:
    home = _setup_home(tmp_path)
    store = TaskStore(home)
    task = Task(task_id="t1", title="Task", description="Need a plan", task_type="general")
    store.create(task)

    io = FakeIO(answers=["Goal text", "END", "Deliverable text", "END", "Audience text", "END", "Deadline text", "END", "Success 1", "END", "Constraints 1", "END", "Inputs 1", "END", "n", "n"])
    run_task(task.task_id, config={}, home=home, io=io)

    task_payload = json.loads((home / "tasks" / task.task_id / "task.json").read_text(encoding="utf-8"))
    assert task_payload["state"] == TaskState.NEEDS_CLARIFICATION.value
    triage_dir = home / "tasks" / task.task_id / "01_triage"
    assert (triage_dir / "initial_brief.json").exists()
    assert (triage_dir / "draft_brief.json").exists()
    assert not (triage_dir / "final_brief.json").exists()
    assert (triage_dir / "iterations.jsonl").exists()
