from pathlib import Path

from data_swarm.orchestrator.runner import run_task
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_kb_apply_prompt_disabled_in_calibration(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / ".data_swarm"
    for part in ["tasks", "memory", "indexes", "logs", "kb"]:
        (home / part).mkdir(parents=True, exist_ok=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    store = TaskStore(home)
    task = Task(task_id="rm1", title="t", description="d", state=TaskState.READY_TO_DELIVER, run_mode="CALIBRATION")
    store.create(task)

    monkeypatch.setattr("data_swarm.orchestrator.runner.run_deliverable", lambda task, task_dir, merged_config, io: (task_dir / "07_deliverable" / "summary.md").write_text("ok", encoding="utf-8"))
    calls = {"apply": 0}
    monkeypatch.setattr("data_swarm.orchestrator.runner.Anonymizer.apply_proposal", lambda self, io: calls.__setitem__("apply", calls["apply"] + 1))
    io = FakeIO(answers=["y"])
    run_task(task.task_id, config={}, home=home, io=io)
    assert calls["apply"] == 0
