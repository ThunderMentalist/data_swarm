from pathlib import Path

from data_swarm.orchestrator.runner import run_task
from data_swarm.orchestrator.task_models import Task
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


def test_triage_stage_resume_appends_history(tmp_path: Path) -> None:
    home = _setup_home(tmp_path)
    store = TaskStore(home)
    task = Task(task_id="t3", title="Task", description="Need a plan", task_type="general")
    store.create(task)

    first_answers = [
        "",
        "Goal text",
        "END",
        "Deliverable text",
        "END",
        "Audience",
        "END",
        "Deadline",
        "END",
        "Success",
        "END",
        "Constraints",
        "END",
        "Inputs",
        "END",
        "n",
    ]
    first_io = FakeIO(answers=first_answers)
    run_task(task.task_id, config={}, home=home, io=first_io)
    history_path = home / "tasks" / task.task_id / "01_triage" / "brief_history.jsonl"
    first_count = len([line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()])

    second_io = FakeIO(
        answers=["", "END", "", "END", "", "END", "y", "deadline", "END", "success", "END", "risk", "END", "dep", "END", "y", "", "END", "y", "first", "END", "seq", "END", "risk", "END", "", "END", "y", "", "END", "", "END", "", "END", "", "END", "y", "", ""]
    )
    run_task(task.task_id, config={}, home=home, io=second_io)
    second_count = len([line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()])

    assert second_count > first_count
    assert (home / "tasks" / task.task_id / "01_triage" / "final_brief.json").exists()
