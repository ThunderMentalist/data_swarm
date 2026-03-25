import json
from pathlib import Path

from data_swarm.orchestrator.run_mode import RunMode, policy_for_mode
from data_swarm.orchestrator.runner import run_task
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.base import StageResult
from data_swarm.stages.readiness.stage import ReadinessStage
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_auto_ready_disabled_by_default() -> None:
    assert policy_for_mode(RunMode.INITIAL_USING).allow_auto_ready_to_deliver is False


def test_readiness_replanning_recommendation(tmp_path: Path) -> None:
    task = Task(task_id="r1", title="t", description="d", state=TaskState.AWAITING_REPLIES)
    decision_file = tmp_path / "06_reaction" / "final_reaction.json"
    decision_file.parent.mkdir(parents=True)
    decision_file.write_text(json.dumps({"readiness_recommendation": "REPLANNING", "blockers": ["blocked"], "readiness_reason": "blocked"}), encoding="utf-8")
    decision = ReadinessStage({}).evaluate(task, tmp_path)
    assert decision.recommended_state == "REPLANNING"


def test_runner_manual_approval_to_delivered(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / ".data_swarm"
    for part in ["tasks", "memory", "indexes", "logs", "kb"]:
        (home / part).mkdir(parents=True, exist_ok=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    store = TaskStore(home)
    task = Task(task_id="d1", title="Deliver", description="desc", state=TaskState.READY_TO_DELIVER)
    task_dir = store.create(task)

    def fake_deliverable(task_obj, task_dir_obj, merged_config, io):
        (task_dir_obj / "07_deliverable" / "summary.md").write_text("ok", encoding="utf-8")

    monkeypatch.setattr("data_swarm.orchestrator.runner.run_deliverable", fake_deliverable)
    io = FakeIO(answers=["y"])
    run_task(task.task_id, config={}, home=home, io=io)
    assert store.load(task.task_id).state == TaskState.DELIVERED


def test_runner_readiness_recommendation_needs_operator(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / ".data_swarm"
    for part in ["tasks", "memory", "indexes", "logs", "kb"]:
        (home / part).mkdir(parents=True, exist_ok=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    store = TaskStore(home)
    task = Task(task_id="a1", title="Await", description="desc", state=TaskState.AWAITING_REPLIES)
    store.create(task)

    class DummyReaction:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, task, task_dir, kb, attachments, **kwargs):
            out = task_dir / "06_reaction" / "final_reaction.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"readiness_recommendation": "READY_TO_DELIVER", "blockers": [], "readiness_reason": "clear"}), encoding="utf-8")
            return StageResult(True, task.state, ["06_reaction/final_reaction.json"])

    class DummyStage:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, task, task_dir, kb, attachments, **kwargs):
            return StageResult(False, task.state, [])

    monkeypatch.setattr("data_swarm.orchestrator.runner.ReactionStage", DummyReaction)
    monkeypatch.setattr("data_swarm.orchestrator.runner.IntakeRefineStage", DummyStage)
    monkeypatch.setattr("data_swarm.orchestrator.runner.TriageStage", DummyStage)
    monkeypatch.setattr("data_swarm.orchestrator.runner.PlannerStage", DummyStage)
    monkeypatch.setattr("data_swarm.orchestrator.runner.StakeholderStage", DummyStage)
    monkeypatch.setattr("data_swarm.orchestrator.runner.NavigationStage", DummyStage)
    monkeypatch.setattr("data_swarm.orchestrator.runner.CommsStage", DummyStage)

    io = FakeIO(answers=["n"])
    run_task(task.task_id, config={}, home=home, io=io)
    assert store.load(task.task_id).state == TaskState.AWAITING_REPLIES
