"""Stakeholder stage orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm import yaml_compat as yaml
from data_swarm.orchestrator.hitl import ask_multiline, ask_yes_no
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.stakeholder.change import StakeholderChangeAgent
from data_swarm.stages.stakeholder.concierge import StakeholderConciergeAgent
from data_swarm.stages.stakeholder.critic import StakeholderCriticAgent
from data_swarm.stages.stakeholder.curator import StakeholderCuratorAgent
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import UserIO


class StakeholderStage(AgenticStage):
    """Agentic stakeholder mapping stage with approval gate."""

    name = "stakeholder"

    def __init__(self, config: dict, home: Path, io: UserIO, store: TaskStore, logs: LogStore) -> None:
        self.config = config
        self.home = home
        self.io = io
        self.store = store
        self.logs = logs

    def run(self, task: Task, task_dir: Path) -> StageResult:
        stage_dir = task_dir / "03_stakeholders"
        stage_dir.mkdir(parents=True, exist_ok=True)
        final_path = stage_dir / "03_stakeholders.yaml"
        if final_path.exists():
            return StageResult(True, task.state, ["03_stakeholders/03_stakeholders.yaml"])

        concierge = StakeholderConciergeAgent()
        critic = StakeholderCriticAgent()
        curator = StakeholderCuratorAgent()
        change = StakeholderChangeAgent()
        initial_path = stage_dir / "initial_stakeholders.yaml"
        history_path = stage_dir / "stakeholders_history.jsonl"
        clarification_path = stage_dir / "clarification_log.jsonl"

        if history_path.exists():
            current = self._read_jsonl(history_path)[-1].get("content", "")
        else:
            current = concierge.initial_map()

        artifacts: list[str] = []
        if not initial_path.exists():
            initial_path.write_text(current, encoding="utf-8")
            artifacts.append("03_stakeholders/initial_stakeholders.yaml")
        if not history_path.exists():
            self._append_jsonl(history_path, concierge.snapshot(current))
            artifacts.append("03_stakeholders/stakeholders_history.jsonl")

        edited = ask_multiline(
            self.io,
            "Paste revised stakeholder YAML; END to finish; submit empty (END immediately) to keep current",
        )
        if edited.strip():
            current = edited.strip() + "\n"
            self._append_jsonl(clarification_path, {"note": "manual yaml replacement", "content": "provided"})
        else:
            self._append_jsonl(clarification_path, {"note": "manual yaml replacement", "content": "kept current"})
        artifacts.append("03_stakeholders/clarification_log.jsonl")
        self._append_jsonl(history_path, concierge.snapshot(current))

        self.io.tell("Current stakeholder map:\n" + current)
        if not ask_yes_no(self.io, "Approve this stakeholder map to proceed?", default_no=True):
            target = TaskState.REPLANNING if task.state in {
                TaskState.PLANNED,
                TaskState.OUTREACH_PENDING_REVIEW,
                TaskState.AWAITING_REPLIES,
            } else TaskState.NEEDS_CLARIFICATION
            if task.state != target:
                apply_transition(task, target, "stakeholder map not approved", ["03_stakeholders/stakeholders_history.jsonl"], self.store, self.logs, self.name)
            return StageResult(False, task.state, sorted(set(artifacts)))

        final_path.write_text(current, encoding="utf-8")
        artifacts.append("03_stakeholders/03_stakeholders.yaml")

        initial_yaml = initial_path.read_text(encoding="utf-8")
        critic_eval = critic.evaluate(initial_yaml, current)
        (stage_dir / "stakeholder_critic_eval.json").write_text(json.dumps(critic_eval, indent=2), encoding="utf-8")
        delta_md, candidates_yaml = curator.curate(initial_yaml, current)
        (stage_dir / "delta_learning.md").write_text(delta_md, encoding="utf-8")
        (stage_dir / "learning_candidates.yaml").write_text(candidates_yaml, encoding="utf-8")
        change_request = change.generate(task.task_id, critic_eval, yaml.safe_load(candidates_yaml) or {}, self.home)
        (stage_dir / "change_request.md").write_text(change_request, encoding="utf-8")
        artifacts.extend([
            "03_stakeholders/stakeholder_critic_eval.json",
            "03_stakeholders/delta_learning.md",
            "03_stakeholders/learning_candidates.yaml",
            "03_stakeholders/change_request.md",
        ])
        return StageResult(True, task.state, sorted(set(artifacts)))

    @staticmethod
    def _append_jsonl(path: Path, payload: dict) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict]:
        rows: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows
