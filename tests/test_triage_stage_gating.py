import json
from pathlib import Path

from data_swarm.orchestrator.runner import run_task
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def _setup_home(tmp_path: Path) -> Path:
    home = tmp_path / ".data_swarm"
    for part in ["tasks", "memory", "indexes", "logs"]:
        (home / part).mkdir(parents=True, exist_ok=True)
    (home / "tone_profile.md").write_text("tone", encoding="utf-8")
    (home / "triage_policy" / "active" / "behaviour_cards").mkdir(parents=True, exist_ok=True)
    (home / "triage_policy" / "active" / "decision_trees").mkdir(parents=True, exist_ok=True)
    (home / "triage_policy" / "history").mkdir(parents=True, exist_ok=True)
    (home / "triage_policy" / "history" / "triage_change_requests.jsonl").touch()
    (home / "triage_policy" / "history" / "repetition_index.json").write_text("{}", encoding="utf-8")
    return home


def test_triage_stage_stops_pipeline_when_not_approved(tmp_path: Path) -> None:
    home = _setup_home(tmp_path)
    store = TaskStore(home)
    task = Task(task_id="t1", title="Task", description="Need a plan", task_type="general")
    store.create(task)

    io = FakeIO(
        answers=[
            "",  # intake additional names prompt
            "Goal text",
            "END",
            "Deliverable text",
            "END",
            "Audience text",
            "END",
            "Deadline text",
            "END",
            "Success 1",
            "END",
            "Constraints 1",
            "END",
            "Inputs 1",
            "END",
            "n",
        ]
    )

    run_task(task.task_id, config={}, home=home, io=io)

    task_payload = json.loads((home / "tasks" / task.task_id / "task.json").read_text(encoding="utf-8"))
    assert task_payload["state"] == TaskState.NEEDS_CLARIFICATION.value
    triage_dir = home / "tasks" / task.task_id / "01_triage"
    assert (triage_dir / "initial_brief.json").exists()
    assert (triage_dir / "brief_history.jsonl").exists()
    assert not (triage_dir / "final_brief.json").exists()
    assert not (home / "tasks" / task.task_id / "02_plan" / "02_plan.md").exists()
