import json
from pathlib import Path

from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.orchestrator.runner import run_task
from data_swarm.projects.meridian_aux.project import MeridianAuxProject
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def _base_config(tmp_path: Path) -> dict:
    meridian = tmp_path / "meridian"
    meridian_aux = tmp_path / "meridian_aux"
    meridian.mkdir()
    meridian_aux.mkdir()
    return {
        "data_swarm_home": str(tmp_path),
        "paths": {"meridian_repo": str(meridian), "meridian_aux_repo": str(meridian_aux)},
        "llm": {
            "provider": "openai",
            "defaults": {"model": "dummy", "reasoning_effort": "medium", "verbosity": "medium"},
            "profiles": {
                "meridian.codegen": {"model": "dummy.codegen", "reasoning_effort": "high", "verbosity": "medium"},
                "meridian.debugger": {"model": "dummy.debugger", "reasoning_effort": "high", "verbosity": "low"},
            },
        },
        "meridian_aux": {"max_files": 2, "max_chars": 200, "max_debug_iterations": 1},
    }


def test_patch_not_applied_without_approval(tmp_path: Path, monkeypatch) -> None:
    cfg = _base_config(tmp_path)
    task = Task(task_id="m1", title="t", description="d")
    task_dir = tmp_path / "task"
    (task_dir / "07_deliverable").mkdir(parents=True)

    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.build_index", lambda *a, **k: None)
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.dependency_closure", lambda *a, **k: ([('meridian_aux','x.py')], []))
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.NavigatorAgent.decide", lambda *a, **k: {"entrypoints": [{"repo": "meridian_aux", "file_path": "x.py"}]})
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.RetrieverAgent.retrieve", lambda *a, **k: ({}, 0))
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.CodegenAgent.generate", lambda *a, **k: {"patch": "diff --git a/x b/x\n", "snippet": "print(1)", "tests_added": [], "notes": "n"})
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.run_snippet", lambda *a, **k: (0, "", ""))
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.run_pytest", lambda *a, **k: (0, "", ""))

    called = {"applied": False}
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.apply_patch_safe", lambda *a, **k: called.__setitem__("applied", True))

    io = FakeIO(answers=["n"])
    MeridianAuxProject(cfg, io).run(task, task_dir)
    assert called["applied"] is False


def test_debug_loop_bounded_and_failure_artifacts(tmp_path: Path, monkeypatch) -> None:
    cfg = _base_config(tmp_path)
    task = Task(task_id="m2", title="t", description="d")
    task_dir = tmp_path / "task2"
    (task_dir / "07_deliverable").mkdir(parents=True)

    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.build_index", lambda *a, **k: None)
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.dependency_closure", lambda *a, **k: ([('meridian_aux','x.py')], []))
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.NavigatorAgent.decide", lambda *a, **k: {"entrypoints": [{"repo": "meridian_aux", "file_path": "x.py"}]})
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.RetrieverAgent.retrieve", lambda *a, **k: ({}, 0))
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.CodegenAgent.generate", lambda *a, **k: {"patch": "", "snippet": "print(1)", "tests_added": [], "notes": "n"})
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.DebuggerAgent.propose", lambda *a, **k: {"patch": "", "notes": "debug"})
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.run_snippet", lambda *a, **k: (1, "", "err"))
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.run_pytest", lambda *a, **k: (1, "", "perr"))

    io = FakeIO(answers=["y"])
    MeridianAuxProject(cfg, io).run(task, task_dir)
    assert (task_dir / "07_deliverable" / "traceback.txt").exists()
    run_data = json.loads((task_dir / "07_deliverable" / "test_run.json").read_text(encoding="utf-8"))
    assert run_data["iteration"] <= 1


def test_runner_transitions_delivered_when_ready(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / ".data_swarm"
    for part in ["tasks", "memory", "indexes", "logs", "kb"]:
        (home / part).mkdir(parents=True, exist_ok=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    store = TaskStore(home)
    task = Task(task_id="done1", title="done", description="d", state=TaskState.READY_TO_DELIVER)
    task_dir = store.create(task)

    monkeypatch.setattr("data_swarm.orchestrator.runner.run_deliverable", lambda task, task_dir, merged_config, io: (task_dir / "07_deliverable" / "summary.md").write_text("ok", encoding="utf-8"))
    io = FakeIO(answers=["y"])
    run_task(task.task_id, config={}, home=home, io=io)
    assert store.load(task.task_id).state == TaskState.DELIVERED
