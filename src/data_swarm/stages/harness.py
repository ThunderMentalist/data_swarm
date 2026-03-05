"""Shared stage orchestration harness."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from data_swarm.orchestrator.hitl import ask_yes_no
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.base import StageResult
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO


@dataclass
class StageSpec:
    """Declarative stage definition for the shared harness."""

    stage_key: str
    stage_dir: str
    initial_name: str
    draft_name: str
    final_name: str
    expected_transitions_on_approval: list[TaskState]
    non_approval_target: Callable[[Task], TaskState]


@dataclass
class StageContext:
    """Common context passed into callbacks."""

    task: Task
    task_dir: Path
    stage_dir: Path
    io: UserIO
    attachments: list[dict[str, Any]]
    kb: dict[str, Any]
    policy: dict[str, Any]


class StageHarness:
    """Centralized orchestration for HITL-first stages."""

    def __init__(self, spec: StageSpec, io: UserIO, store: TaskStore, logs: LogStore, anonymizer: Anonymizer) -> None:
        self.spec = spec
        self.io = io
        self.store = store
        self.logs = logs
        self.anonymizer = anonymizer

    def run(
        self,
        task: Task,
        task_dir: Path,
        kb: dict[str, Any],
        policy: dict[str, Any],
        attachments: list[dict[str, Any]],
        make_initial: Callable[[StageContext], Any],
        update_draft_via_hitl: Callable[[StageContext, Any], tuple[Any, dict[str, Any]]],
        render_final: Callable[[StageContext, Any], Any],
        post_approval: Callable[[StageContext, Any, Any], dict[str, Any]],
    ) -> StageResult:
        stage_dir = task_dir / self.spec.stage_dir
        stage_dir.mkdir(parents=True, exist_ok=True)
        initial_path = stage_dir / self.spec.initial_name
        draft_path = stage_dir / self.spec.draft_name
        final_path = stage_dir / self.spec.final_name
        iteration_path = stage_dir / "iterations.jsonl"
        learning_path = stage_dir / "learning_summary.md"
        manifest_path = stage_dir / "manifest.json"

        ctx = StageContext(task=task, task_dir=task_dir, stage_dir=stage_dir, io=self.io, attachments=attachments, kb=kb, policy=policy)

        artifacts: list[str] = []
        if final_path.exists():
            self._reconcile_state(task)
            self.logs.event(task.task_id, self.spec.stage_key, "stage_complete", "stage resumed from final artifact", {
                "approved": True,
                "state_after": task.state.value,
                "artifacts_written": [self._rel(task_dir, final_path)],
            })
            return StageResult(True, task.state, [self._rel(task_dir, final_path)])

        started_at = _utc_now()
        if draft_path.exists():
            draft = self._read_any(draft_path)
        else:
            initial = make_initial(ctx)
            self._write_any(initial_path, initial)
            artifacts.append(self._rel(task_dir, initial_path))
            draft = initial
            self._write_any(draft_path, draft)
            artifacts.append(self._rel(task_dir, draft_path))

        draft, learning = update_draft_via_hitl(ctx, draft)
        self._write_any(draft_path, draft)
        artifacts.append(self._rel(task_dir, draft_path))

        approved = ask_yes_no(self.io, f"Approve {self.spec.stage_key} output to proceed?", default_no=True)
        decisions = learning.get("decisions", [])
        resolved_unknowns = learning.get("resolved_unknowns", [])
        remaining_unknowns = learning.get("remaining_unknowns", [])
        summary = learning.get("learning_summary", "No additional learning captured.")

        if not approved:
            target = self.spec.non_approval_target(task)
            if task.state != target:
                apply_transition(task, target, f"{self.spec.stage_key} not approved", [self._rel(task_dir, draft_path)], self.store, self.logs, self.spec.stage_key)
            self._append_iteration(iteration_path, started_at, False, summary, decisions, resolved_unknowns, remaining_unknowns, attachments, kb, artifacts)
            learning_path.write_text(summary + "\n", encoding="utf-8")
            artifacts.extend([self._rel(task_dir, iteration_path), self._rel(task_dir, learning_path)])
            self._write_manifest(task_dir, manifest_path, artifacts)
            artifacts.append(self._rel(task_dir, manifest_path))
            return StageResult(False, task.state, sorted(set(artifacts)))

        final_payload = render_final(ctx, draft)
        self._write_any(final_path, final_payload)
        artifacts.append(self._rel(task_dir, final_path))

        for target in self.spec.expected_transitions_on_approval:
            if task.state != target:
                apply_transition(task, target, f"{self.spec.stage_key} approved", [self._rel(task_dir, final_path)], self.store, self.logs, self.spec.stage_key)

        extra = post_approval(ctx, self._read_or_none(initial_path), final_payload)
        for rel, payload in extra.items():
            out = task_dir / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            self._write_any(out, payload)
            artifacts.append(rel)

        learning_path.write_text(summary + "\n", encoding="utf-8")
        artifacts.append(self._rel(task_dir, learning_path))
        self._append_iteration(iteration_path, started_at, True, summary, decisions, resolved_unknowns, remaining_unknowns, attachments, kb, artifacts)
        artifacts.append(self._rel(task_dir, iteration_path))
        self._write_manifest(task_dir, manifest_path, artifacts)
        artifacts.append(self._rel(task_dir, manifest_path))

        self.logs.event(task.task_id, self.spec.stage_key, "stage_complete", f"{self.spec.stage_key} complete", {
            "approved": True,
            "state_after": task.state.value,
            "artifacts_written": sorted(set(artifacts)),
        })
        return StageResult(True, task.state, sorted(set(artifacts)))

    def _reconcile_state(self, task: Task) -> None:
        for target in self.spec.expected_transitions_on_approval:
            if task.state == target:
                continue
            should_apply = ask_yes_no(self.io, f"Found completed {self.spec.stage_key} artifact but task state is {task.state.value}. Apply missing transition to {target.value}?", default_no=True)
            if should_apply:
                apply_transition(task, target, f"resume reconciliation for {self.spec.stage_key}", [], self.store, self.logs, self.spec.stage_key)

    def _append_iteration(
        self,
        path: Path,
        started_at: str,
        approved: bool,
        summary: str,
        decisions: list[str],
        resolved_unknowns: list[str],
        remaining_unknowns: list[str],
        attachments: list[dict[str, Any]],
        kb: dict[str, Any],
        artifacts: list[str],
    ) -> None:
        payload = {
            "started_at": started_at,
            "ended_at": _utc_now(),
            "approved": approved,
            "learning_summary": self.anonymizer.sanitize_text(summary)[0],
            "decisions": [self.anonymizer.sanitize_text(d)[0] for d in decisions],
            "resolved_unknowns": [self.anonymizer.sanitize_text(x)[0] for x in resolved_unknowns],
            "remaining_unknowns": [self.anonymizer.sanitize_text(x)[0] for x in remaining_unknowns],
            "inputs_used": {
                "kb_keys": sorted(kb.keys()),
                "attachment_hashes": [item.get("sha256", "") for item in attachments],
            },
            "artifacts_written": sorted(set(artifacts)),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def _write_manifest(self, task_dir: Path, path: Path, rel_artifacts: list[str]) -> None:
        entries: list[dict[str, str]] = []
        for rel in sorted(set(rel_artifacts)):
            full = task_dir / rel
            if not full.exists() or full == path:
                continue
            entries.append({"path": rel, "sha256": _hash_file(full)})
        path.write_text(json.dumps({"artifacts": entries}, indent=2), encoding="utf-8")

    @staticmethod
    def _write_any(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, (dict, list)):
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return
        path.write_text(str(payload), encoding="utf-8")

    @staticmethod
    def _read_any(path: Path) -> Any:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            return json.loads(text)
        return text

    @staticmethod
    def _read_or_none(path: Path) -> Any:
        if not path.exists():
            return None
        return StageHarness._read_any(path)

    @staticmethod
    def _rel(task_dir: Path, path: Path) -> str:
        return str(path.relative_to(task_dir))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()
