"""Shared stage orchestration harness."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from data_swarm.orchestrator.hitl import StageGateAction, ask_multiline, stage_gate
from data_swarm.orchestrator.run_mode import RunMode, RunModePolicy
from data_swarm.orchestrator.state_machine import InvalidTransitionError
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.base import StageResult
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.memory_store import MemoryStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO


@dataclass
class StageSpec:
    stage_key: str
    stage_dir: str
    initial_name: str
    draft_name: str
    final_name: str
    expected_transitions_on_approval: list[TaskState]


@dataclass
class StageContext:
    task: Task
    task_dir: Path
    stage_dir: Path
    cycle_dir: Path
    io: UserIO
    attachments: list[dict[str, Any]]
    kb: dict[str, Any]
    policy: dict[str, Any]
    memory_store: MemoryStore | None
    run_mode: RunMode
    run_mode_policy: RunModePolicy
    repo_root: Path
    cycle_id: int


def cycle_dir(stage_dir: Path, cycle_id: int) -> Path:
    return stage_dir / f"cycle_{cycle_id:04d}"


class StageHarness:
    def __init__(self, spec: StageSpec, io: UserIO, store: TaskStore, logs: LogStore, anonymizer: Anonymizer) -> None:
        self.spec = spec
        self.io = io
        self.store = store
        self.logs = logs
        self.anonymizer = anonymizer

    def run(self, task: Task, task_dir: Path, kb: dict[str, Any], policy: dict[str, Any], attachments: list[dict[str, Any]],
            make_initial: Callable[[StageContext], Any], update_draft_via_hitl: Callable[[StageContext, Any], tuple[Any, dict[str, Any]]],
            render_final: Callable[[StageContext, Any], Any], post_approval: Callable[[StageContext, Any, Any], dict[str, Any]],
            memory_store: MemoryStore | None = None, run_mode: RunMode = RunMode.INITIAL_USING,
            run_mode_policy: RunModePolicy | None = None, repo_root: Path | None = None) -> StageResult:
        run_mode_policy = run_mode_policy or RunModePolicy(True, True, True, True, False, False, True)
        stage_dir = task_dir / self.spec.stage_dir
        stage_dir.mkdir(parents=True, exist_ok=True)
        cdir = cycle_dir(stage_dir, task.cycle_id)
        cdir.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy(stage_dir, cdir)

        initial_path, draft_path, final_path = cdir / self.spec.initial_name, cdir / self.spec.draft_name, cdir / self.spec.final_name
        iteration_path, learning_path, manifest_path = cdir / "iterations.jsonl", cdir / "learning_summary.md", cdir / "manifest.json"
        ctx = StageContext(task, task_dir, stage_dir, cdir, self.io, attachments, kb, policy, memory_store, run_mode, run_mode_policy, repo_root or task_dir, task.cycle_id)

        artifacts: list[str] = []
        if final_path.exists():
            for target in self.spec.expected_transitions_on_approval:
                if task.state != target:
                    self._safe_transition(task, target, f"resume reconciliation for {self.spec.stage_key}", [self._rel(task_dir, final_path)])
            self.logs.event(task.task_id, self.spec.stage_key, "stage_resumed_from_final", "stage resumed from final artifact", {"artifact": self._rel(task_dir, final_path)})
            return StageResult(True, task.state, [self._rel(task_dir, final_path)])

        started_at = _utc_now()
        draft = self._read_any(draft_path) if draft_path.exists() else make_initial(ctx)
        if not draft_path.exists():
            self._write_any(initial_path, draft)
            artifacts.append(self._rel(task_dir, initial_path))

        approved = False
        skipped = False
        learning = {"learning_summary": ""}
        while True:
            draft, learning = update_draft_via_hitl(ctx, draft)
            self._write_any(draft_path, draft)
            artifacts.append(self._rel(task_dir, draft_path))
            action = stage_gate(self.io, self.spec.stage_key)
            self.logs.event(task.task_id, self.spec.stage_key, "stage_gate_decision", "stage gate decision", {"action": action.value})
            if action is StageGateAction.REVISE_STAGE:
                self._append_iteration(iteration_path, started_at, False, learning.get("learning_summary", ""), [], [], [], attachments, kb, artifacts)
                self.logs.event(task.task_id, self.spec.stage_key, "stage_iteration_complete", "stage revised")
                continue
            if action is StageGateAction.SKIP_STAGE:
                note = ask_multiline(self.io, f"Optional reason for skipping {self.spec.stage_key}")
                (cdir / "skipped.md").write_text(note or "Skipped by operator.\n", encoding="utf-8")
                artifacts.append(self._rel(task_dir, cdir / "skipped.md"))
                approved, skipped = True, True
                break
            if action is StageGateAction.PAUSE_BLOCKED:
                self._safe_transition(task, TaskState.BLOCKED, f"{self.spec.stage_key} paused by operator", [self._rel(task_dir, draft_path)])
                self._append_iteration(iteration_path, started_at, False, learning.get("learning_summary", ""), [], [], [], attachments, kb, artifacts)
                return StageResult(False, task.state, sorted(set(artifacts)))
            if action is StageGateAction.CLOSE_EARLY:
                self._safe_transition(task, TaskState.CLOSED, f"{self.spec.stage_key} closed early by operator", [self._rel(task_dir, draft_path)])
                self._append_iteration(iteration_path, started_at, False, learning.get("learning_summary", ""), [], [], [], attachments, kb, artifacts)
                return StageResult(False, task.state, sorted(set(artifacts)))
            approved = True
            break

        if approved and not skipped:
            final_payload = render_final(ctx, draft)
            self._write_any(final_path, final_payload)
            artifacts.append(self._rel(task_dir, final_path))
            for target in self.spec.expected_transitions_on_approval:
                if task.state != target:
                    self._safe_transition(task, target, f"{self.spec.stage_key} approved", [self._rel(task_dir, final_path)])
            extra = post_approval(ctx, self._read_or_none(initial_path), final_payload)
            for rel, payload in extra.items():
                out = task_dir / rel if not str(rel).startswith(self.spec.stage_dir) else task_dir / rel
                if not out.is_absolute() and str(rel).startswith(self.spec.stage_dir + "/"):
                    pass
                out.parent.mkdir(parents=True, exist_ok=True)
                self._write_any(out, payload)
                artifacts.append(str(out.relative_to(task_dir)))

        learning_path.write_text((learning.get("learning_summary") or "No additional learning captured.") + "\n", encoding="utf-8")
        artifacts.append(self._rel(task_dir, learning_path))
        self._append_iteration(iteration_path, started_at, approved, learning.get("learning_summary", ""), learning.get("decisions", []), learning.get("resolved_unknowns", []), learning.get("remaining_unknowns", []), attachments, kb, artifacts)
        artifacts.append(self._rel(task_dir, iteration_path))
        self._write_manifest(task_dir, manifest_path, artifacts)
        artifacts.append(self._rel(task_dir, manifest_path))
        return StageResult(True, task.state, sorted(set(artifacts)), skipped=skipped)

    def _safe_transition(self, task: Task, target: TaskState, reason: str, artifacts: list[str]) -> None:
        try:
            if task.state != target:
                apply_transition(task, target, reason, artifacts, self.store, self.logs, self.spec.stage_key)
        except InvalidTransitionError as exc:
            self.logs.event(task.task_id, self.spec.stage_key, "invalid_transition", str(exc), {"fallback": "BLOCKED"})
            if task.state != TaskState.BLOCKED:
                apply_transition(task, TaskState.BLOCKED, f"fallback blocked: {reason}", artifacts, self.store, self.logs, self.spec.stage_key)

    def _migrate_legacy(self, stage_dir: Path, cdir: Path) -> None:
        if cdir.exists() and any(cdir.iterdir()):
            return
        for name in [self.spec.initial_name, self.spec.draft_name, self.spec.final_name, "iterations.jsonl", "learning_summary.md", "manifest.json"]:
            legacy = stage_dir / name
            if legacy.exists() and not (cdir / name).exists():
                (cdir / name).write_bytes(legacy.read_bytes())

    def _append_iteration(self, path: Path, started_at: str, approved: bool, summary: str, decisions: list[str], resolved_unknowns: list[str], remaining_unknowns: list[str], attachments: list[dict[str, Any]], kb: dict[str, Any], artifacts: list[str]) -> None:
        payload = {"started_at": started_at, "ended_at": _utc_now(), "approved": approved, "learning_summary": self.anonymizer.sanitize_text(summary)[0], "decisions": [self.anonymizer.sanitize_text(d)[0] for d in decisions], "resolved_unknowns": [self.anonymizer.sanitize_text(x)[0] for x in resolved_unknowns], "remaining_unknowns": [self.anonymizer.sanitize_text(x)[0] for x in remaining_unknowns], "inputs_used": {"kb_keys": sorted(kb.keys()), "attachment_hashes": [item.get("sha256", "") for item in attachments]}, "artifacts_written": sorted(set(artifacts))}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def _write_manifest(self, task_dir: Path, path: Path, rel_artifacts: list[str]) -> None:
        entries = []
        for rel in sorted(set(rel_artifacts)):
            full = task_dir / rel
            if full.exists() and full != path:
                entries.append({"path": rel, "sha256": _hash_file(full)})
        path.write_text(json.dumps({"artifacts": entries}, indent=2), encoding="utf-8")

    @staticmethod
    def _write_any(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, (dict, list)):
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        else:
            path.write_text(str(payload), encoding="utf-8")

    @staticmethod
    def _read_any(path: Path) -> Any:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            return json.loads(text)
        return text

    @staticmethod
    def _read_or_none(path: Path) -> Any:
        return StageHarness._read_any(path) if path.exists() else None

    @staticmethod
    def _rel(task_dir: Path, path: Path) -> str:
        return str(path.relative_to(task_dir))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
