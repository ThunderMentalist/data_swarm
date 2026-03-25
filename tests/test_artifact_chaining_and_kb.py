import json
from pathlib import Path

from data_swarm.kb import select_stage_kb_context
from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.artifacts import load_stage_inputs
from data_swarm.stages.planner.stage import PlannerStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def test_stage_kb_selector_returns_stage_subset() -> None:
    kb = {"role_registry": {"x": 1}, "org_units": {"y": 2}, "personas": {"z": 3}, "extra": {"n": 4}}
    subset = select_stage_kb_context("triage", kb)
    assert set(subset.keys()) == {"role_registry", "org_units", "personas", "stakeholder_profiles"}


def test_planner_consumes_triage_artifact(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    (home / "kb").mkdir(parents=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    store = TaskStore(home)
    from data_swarm.orchestrator.task_models import TaskState
    task = Task(task_id="p1", title="Runner", description="desc", state=TaskState.TRIAGED)
    task_dir = store.create(task)
    (task_dir / "01_triage" / "final_brief.json").write_text(json.dumps({"goal": "ship demo", "constraints": [], "risks": [], "success_criteria": []}), encoding="utf-8")
    io = FakeIO(answers=["END", "END", "END", "END", "1"])
    stage = PlannerStage(config={}, home=home, io=io, store=store, logs=LogStore(task_dir))
    result = stage.run(task, task_dir, kb={})
    assert result.approved is True
    payload = json.loads((task_dir / "02_plan" / "cycle_0001" / "02_plan.json").read_text(encoding="utf-8"))
    assert payload["objective"] == "ship demo"


def test_load_stage_inputs_chain(tmp_path: Path) -> None:
    task_dir = tmp_path
    for rel, payload in [
        ("01_triage/final_brief.json", {"goal": "a"}),
        ("02_plan/02_plan.json", {"objective": "b"}),
        ("03_stakeholders/03_stakeholders.json", {"roles": []}),
    ]:
        path = task_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
    data = load_stage_inputs(task_dir)
    assert data["triage"]["goal"] == "a"
    assert data["planner"]["objective"] == "b"
