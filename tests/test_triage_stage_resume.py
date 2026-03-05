from pathlib import Path

from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.triage.stage import TriageStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_triage_stage_resume_reconciles_state(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    for part in ["tasks", "kb"]:
        (home / part).mkdir(parents=True, exist_ok=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")

    store = TaskStore(home)
    task = Task(task_id="t3", title="Task", description="Need a plan", task_type="general")
    task_dir = store.create(task)
    triage_dir = task_dir / "01_triage"
    (triage_dir / "final_brief.json").write_text("{}", encoding="utf-8")

    io = FakeIO(answers=["y"])
    stage = TriageStage(config={}, home=home, io=io, store=store, logs=LogStore(task_dir))
    result = stage.run(task, task_dir)

    assert result.approved is True
    assert store.load(task.task_id).state == TaskState.TRIAGED
