from __future__ import annotations

from pathlib import Path

import pytest

from data_swarm.llm import LLMProfile, OpenAIProvider, resolve_llm_profile
from data_swarm.orchestrator.execution_context import ExecutionContext
from data_swarm.projects.meridian_aux.project import MeridianAuxProject
from data_swarm.stages.triage.stage import TriageStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import FakeIO


def _config() -> dict:
    return {
        "llm": {
            "provider": "openai",
            "defaults": {
                "model": "default-model",
                "reasoning_effort": "medium",
                "verbosity": "medium",
                "max_output_tokens": 321,
            },
            "profiles": {
                "meridian.codegen": {"model": "code-model", "reasoning_effort": "high"},
                "triage.concierge": {"model": "triage-model", "verbosity": "low"},
            },
        }
    }


def test_resolve_llm_profile_direct_and_inheritance() -> None:
    profile = resolve_llm_profile(_config(), "meridian.codegen")
    assert profile.model == "code-model"
    assert profile.reasoning_effort == "high"
    assert profile.verbosity == "medium"
    assert profile.max_output_tokens == 321


def test_resolve_llm_profile_missing_key_uses_defaults() -> None:
    profile = resolve_llm_profile(_config(), "not.configured")
    assert profile.model == "default-model"
    assert profile.reasoning_effort == "medium"


def test_resolve_llm_profile_raises_without_any_model() -> None:
    with pytest.raises(KeyError):
        resolve_llm_profile({"llm": {"defaults": {}, "profiles": {}}}, "x")


def test_openai_provider_builds_responses_payload_from_profile() -> None:
    provider = OpenAIProvider(LLMProfile(model="x", reasoning_effort="high", verbosity="low", max_output_tokens=88))
    payload = provider._request_payload("hello")
    assert payload == {
        "model": "x",
        "input": "hello",
        "reasoning": {"effort": "high"},
        "text": {"verbosity": "low"},
        "max_output_tokens": 88,
    }


def test_execution_context_routes_profile_into_stage(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / "kb").mkdir(parents=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    task_dir = home / "tasks"
    task_dir.mkdir(parents=True)

    context = ExecutionContext(config=_config())
    store = TaskStore(home)
    logs = LogStore(task_dir, anonymizer=Anonymizer(home / "kb" / "personas.yaml"))

    stage = TriageStage(
        config=_config(),
        home=home,
        io=FakeIO(),
        store=store,
        logs=logs,
        execution_context=context,
    )
    assert stage.concierge_profile is not None
    assert stage.concierge_profile.model == "triage-model"


def test_meridian_project_routes_codegen_and_debugger_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    meridian = tmp_path / "meridian"
    meridian_aux = tmp_path / "meridian_aux"
    meridian.mkdir()
    meridian_aux.mkdir()
    task_dir = tmp_path / "task"
    (task_dir / "07_deliverable").mkdir(parents=True)

    cfg = {
        "data_swarm_home": str(tmp_path),
        "paths": {"meridian_repo": str(meridian), "meridian_aux_repo": str(meridian_aux)},
        "llm": {
            "provider": "openai",
            "defaults": {"model": "default-model", "reasoning_effort": "medium", "verbosity": "medium"},
            "profiles": {
                "meridian.codegen": {"model": "model.codegen", "reasoning_effort": "high", "verbosity": "medium"},
                "meridian.debugger": {"model": "model.debugger", "reasoning_effort": "high", "verbosity": "low"},
            },
        },
        "meridian_aux": {"max_files": 1, "max_chars": 100, "max_debug_iterations": 1},
    }

    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.build_index", lambda *a, **k: None)
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.dependency_closure", lambda *a, **k: ([("meridian_aux", "x.py")], []))
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.NavigatorAgent.decide", lambda *a, **k: {"entrypoints": [{"repo": "meridian_aux", "file_path": "x.py"}]})
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.RetrieverAgent.retrieve", lambda *a, **k: ({}, 0))
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.run_snippet", lambda *a, **k: (1, "", "err"))
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.run_pytest", lambda *a, **k: (1, "", "perr"))

    observed: dict[str, str] = {}

    class FakeCodegenAgent:
        def __init__(self, profile: LLMProfile) -> None:
            observed["codegen"] = profile.model

        def generate(self, *_args, **_kwargs):
            return {"patch": "", "snippet": "print(1)", "tests_added": [], "notes": "n"}

    class FakeDebuggerAgent:
        def __init__(self, profile: LLMProfile) -> None:
            observed["debugger"] = profile.model

        def propose(self, *_args, **_kwargs):
            return {"patch": "", "probe_snippet": "", "notes": "n"}

    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.CodegenAgent", FakeCodegenAgent)
    monkeypatch.setattr("data_swarm.projects.meridian_aux.project.DebuggerAgent", FakeDebuggerAgent)

    from data_swarm.orchestrator.task_models import Task

    MeridianAuxProject(cfg, FakeIO(answers=["y"])).run(Task(task_id="m3", title="t", description="d"), task_dir)
    assert observed == {"codegen": "model.codegen", "debugger": "model.debugger"}
