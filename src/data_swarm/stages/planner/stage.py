"""Planner stage orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm import yaml_compat as yaml
from data_swarm.orchestrator.hitl import ask_multiline, ask_yes_no
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.planner.change import PlannerChangeAgent
from data_swarm.stages.planner.concierge import PlannerConciergeAgent
from data_swarm.stages.planner.critic import PlannerCriticAgent
from data_swarm.stages.planner.curator import PlannerCuratorAgent
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import UserIO


class PlannerStage(AgenticStage):
    """Agentic planner stage with approval gating."""

    name = "planner"

    def __init__(self, config: dict, home: Path, io: UserIO, store: TaskStore, logs: LogStore) -> None:
        self.config = config
        self.home = home
        self.io = io
        self.store = store
        self.logs = logs

    def run(self, task: Task, task_dir: Path) -> StageResult:
        plan_dir = task_dir / "02_plan"
        plan_dir.mkdir(parents=True, exist_ok=True)
        final_path = plan_dir / "02_plan.md"
        if final_path.exists():
            return StageResult(True, task.state, ["02_plan/02_plan.md"])

        concierge = PlannerConciergeAgent()
        critic = PlannerCriticAgent()
        curator = PlannerCuratorAgent()
        change = PlannerChangeAgent()

        initial_path = plan_dir / "initial_plan.md"
        history_path = plan_dir / "plan_history.jsonl"
        clarification_path = plan_dir / "clarification_log.jsonl"

        if history_path.exists():
            rows = self._read_jsonl(history_path)
            current_plan = concierge.load_last_snapshot(rows)
        else:
            current_plan = concierge.initial_plan(task.title)

        artifacts: list[str] = []
        if not initial_path.exists():
            initial_path.write_text(current_plan, encoding="utf-8")
            artifacts.append("02_plan/initial_plan.md")
        if not history_path.exists():
            self._append_jsonl(history_path, concierge.snapshot(current_plan))
            artifacts.append("02_plan/plan_history.jsonl")

        for name in ["assumptions", "unknowns", "dependencies", "next_actions"]:
            placeholder_path = plan_dir / f"{name}.yaml"
            if not placeholder_path.exists():
                placeholder_path.write_text(
                    yaml.safe_dump([{"item": f"{name} placeholder", "owner": "agent"}], sort_keys=False),
                    encoding="utf-8",
                )

        while True:
            qa_round: list[tuple[str, str]] = []
            for question in concierge.next_questions(current_plan):
                answer = ask_multiline(self.io, f"Planning clarification: {question}")
                qa_round.append((question, answer))
                self._append_jsonl(clarification_path, {"question": question, "answer": answer, "edit_summary": "planning clarification"})
            artifacts.append("02_plan/clarification_log.jsonl")
            current_plan = concierge.apply_answers(current_plan, qa_round)
            self._append_jsonl(history_path, concierge.snapshot(current_plan))
            self.io.tell("Current plan:\n" + current_plan)

            if ask_yes_no(self.io, "Approve this plan to proceed?", default_no=True):
                break

            target = TaskState.REPLANNING if task.state in {
                TaskState.PLANNED,
                TaskState.OUTREACH_PENDING_REVIEW,
                TaskState.AWAITING_REPLIES,
            } else TaskState.NEEDS_CLARIFICATION
            if task.state != target:
                apply_transition(task, target, "planner stage not approved", ["02_plan/plan_history.jsonl"], self.store, self.logs, self.name)
            return StageResult(False, task.state, sorted(set(artifacts)))

        final_path.write_text(current_plan, encoding="utf-8")
        artifacts.append("02_plan/02_plan.md")
        if task.state != TaskState.PLANNED:
            apply_transition(task, TaskState.PLANNED, "planning complete", ["02_plan/02_plan.md"], self.store, self.logs, self.name)

        initial_plan = initial_path.read_text(encoding="utf-8")
        critic_eval = critic.evaluate(initial_plan, current_plan)
        (plan_dir / "plan_critic_eval.json").write_text(json.dumps(critic_eval, indent=2), encoding="utf-8")
        artifacts.append("02_plan/plan_critic_eval.json")

        delta_md, candidates_yaml = curator.curate(initial_plan, current_plan)
        (plan_dir / "delta_learning.md").write_text(delta_md, encoding="utf-8")
        (plan_dir / "learning_candidates.yaml").write_text(candidates_yaml, encoding="utf-8")
        artifacts.extend(["02_plan/delta_learning.md", "02_plan/learning_candidates.yaml"])

        candidates_data = yaml.safe_load(candidates_yaml) or {}
        change_request = change.generate(task.task_id, critic_eval, candidates_data, self.home)
        (plan_dir / "change_request.md").write_text(change_request, encoding="utf-8")
        artifacts.append("02_plan/change_request.md")
        return StageResult(True, task.state, sorted(set(artifacts)))

    @staticmethod
    def _append_jsonl(path: Path, payload: dict) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict]:
        out: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out
