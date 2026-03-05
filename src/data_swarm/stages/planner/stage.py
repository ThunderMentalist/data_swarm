"""Planner stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stages.planner.change import PlannerChangeAgent
from data_swarm.stages.planner.concierge import PlannerConciergeAgent
from data_swarm.stages.planner.critic import PlannerCriticAgent
from data_swarm.stages.planner.curator import PlannerCuratorAgent
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO, ConsoleIO


class PlannerStage(AgenticStage):
    name = "planner"

    def __init__(self, config: dict, home: Path, io: UserIO, store: TaskStore, logs: LogStore, anonymizer: Anonymizer | None = None) -> None:
        self.config = config
        self.home = home
        self.io = io
        self.store = store
        self.logs = logs
        self.anonymizer = anonymizer or Anonymizer(home / "kb" / "personas.yaml")

    def run(self, task: Task, task_dir: Path, kb: dict | None = None, attachments: list[dict] | None = None) -> StageResult:
        kb = kb or {}
        attachments = attachments or []
        policy = load_stage_policy(self.home, self.name)
        concierge = PlannerConciergeAgent()
        critic = PlannerCriticAgent()
        curator = PlannerCuratorAgent()
        change = PlannerChangeAgent()
        harness = StageHarness(
            StageSpec("planner", "02_plan", "initial_plan.md", "draft_plan.md", "02_plan.md", [], lambda _t: TaskState.NEEDS_CLARIFICATION),
            self.io,
            self.store,
            self.logs,
            self.anonymizer,
        )

        def make_initial(_ctx):
            return concierge.initial_plan(task.title)

        def update(_ctx, draft):
            qa = []
            for q in concierge.next_questions(draft):
                a = ask_multiline(self.io, f"Planning clarification: {q}")
                qa.append((q, self.anonymizer.collect_from_text(a, self.io)[0]))
            updated = concierge.apply_answers(draft, qa)
            self.io.tell("Current plan:\n" + updated)
            return updated, {"learning_summary": "Plan updated via HITL clarifications.", "decisions": [], "resolved_unknowns": [q for q, a in qa if a], "remaining_unknowns": []}

        def render(_ctx, draft):
            return draft

        def post(_ctx, initial, final):
            critic_eval = critic.evaluate(initial or "", final)
            delta_md, candidates_yaml = curator.curate(initial or "", final)
            return {
                "02_plan/plan_critic_eval.json": critic_eval,
                "02_plan/delta_learning.md": delta_md,
                "02_plan/learning_candidates.yaml": candidates_yaml,
                "02_plan/change_request.md": change.generate(task.task_id, critic_eval, {}, self.home),
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, render, post)
