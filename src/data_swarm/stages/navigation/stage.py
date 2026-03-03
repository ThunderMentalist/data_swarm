"""Navigation stage orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm import yaml_compat as yaml
from data_swarm.agents.navigation import NavigationAgent
from data_swarm.orchestrator.hitl import ask_multiline, ask_yes_no
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.navigation.change import NavigationChangeAgent
from data_swarm.stages.navigation.concierge import NavigationConciergeAgent
from data_swarm.stages.navigation.critic import NavigationCriticAgent
from data_swarm.stages.navigation.curator import NavigationCuratorAgent
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import UserIO


class NavigationStage(AgenticStage):
    """Agentic navigation stage with approval gate."""

    name = "navigation"

    def __init__(self, config: dict, home: Path, io: UserIO, store: TaskStore, logs: LogStore) -> None:
        self.config = config
        self.home = home
        self.io = io
        self.store = store
        self.logs = logs

    def run(self, task: Task, task_dir: Path) -> StageResult:
        stage_dir = task_dir / "04_navigation"
        stage_dir.mkdir(parents=True, exist_ok=True)
        final_path = stage_dir / "04_navigation.md"
        if final_path.exists():
            return StageResult(True, task.state, ["04_navigation/04_navigation.md"])

        concierge = NavigationConciergeAgent()
        critic = NavigationCriticAgent()
        curator = NavigationCuratorAgent()
        change = NavigationChangeAgent()
        initial_path = stage_dir / "initial_navigation.md"
        history_path = stage_dir / "navigation_history.jsonl"
        clarification_path = stage_dir / "clarification_log.jsonl"

        if history_path.exists():
            current = self._read_jsonl(history_path)[-1].get("content", "")
        else:
            current = NavigationAgent().run().content

        artifacts: list[str] = []
        if not initial_path.exists():
            initial_path.write_text(current, encoding="utf-8")
            artifacts.append("04_navigation/initial_navigation.md")
        if not history_path.exists():
            self._append_jsonl(history_path, concierge.snapshot(current))
            artifacts.append("04_navigation/navigation_history.jsonl")

        notes: list[str] = []
        for question in concierge.next_questions():
            answer = ask_multiline(self.io, f"Navigation clarification: {question}")
            notes.append(f"- {question} -> {answer or 'No additional guidance'}")
            self._append_jsonl(clarification_path, {"question": question, "answer": answer, "edit_summary": "navigation clarification"})
        edited = ask_multiline(self.io, "Paste revised navigation section or notes; END to finish; empty keeps generated draft")
        notes_text = "\n".join(notes + ([edited] if edited else []))
        current = concierge.apply_edits(current, notes_text)
        self._append_jsonl(history_path, concierge.snapshot(current))
        artifacts.append("04_navigation/clarification_log.jsonl")

        self.io.tell("Current navigation plan:\n" + current)
        if not ask_yes_no(self.io, "Approve this navigation plan to proceed?", default_no=True):
            target = TaskState.REPLANNING if task.state == TaskState.PLANNED else TaskState.REPLANNING if task.state in {TaskState.OUTREACH_PENDING_REVIEW, TaskState.AWAITING_REPLIES} else TaskState.NEEDS_CLARIFICATION
            if task.state != target:
                apply_transition(task, target, "navigation plan not approved", ["04_navigation/navigation_history.jsonl"], self.store, self.logs, self.name)
            return StageResult(False, task.state, sorted(set(artifacts)))

        final_path.write_text(current, encoding="utf-8")
        artifacts.append("04_navigation/04_navigation.md")
        initial_doc = initial_path.read_text(encoding="utf-8")
        critic_eval = critic.evaluate(initial_doc, current)
        (stage_dir / "navigation_critic_eval.json").write_text(json.dumps(critic_eval, indent=2), encoding="utf-8")
        delta_md, candidates_yaml = curator.curate(initial_doc, current)
        (stage_dir / "delta_learning.md").write_text(delta_md, encoding="utf-8")
        (stage_dir / "learning_candidates.yaml").write_text(candidates_yaml, encoding="utf-8")
        change_request = change.generate(task.task_id, critic_eval, yaml.safe_load(candidates_yaml) or {}, self.home)
        (stage_dir / "change_request.md").write_text(change_request, encoding="utf-8")
        artifacts.extend([
            "04_navigation/navigation_critic_eval.json",
            "04_navigation/delta_learning.md",
            "04_navigation/learning_candidates.yaml",
            "04_navigation/change_request.md",
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
