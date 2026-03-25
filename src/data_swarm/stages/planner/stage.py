"""Planner stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy, select_stage_kb_context
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.artifacts import load_json
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stages.planner.change import PlannerChangeAgent
from data_swarm.stages.planner.critic import PlannerCriticAgent
from data_swarm.stages.planner.curator import PlannerCuratorAgent
from data_swarm.stages.planner.models import PlannerPlan
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO


class PlannerStage(AgenticStage):
    name = "planner"

    def __init__(self, config: dict, home: Path, io: UserIO, store: TaskStore, logs: LogStore, anonymizer: Anonymizer | None = None) -> None:
        self.config = config
        self.home = home
        self.io = io
        self.store = store
        self.logs = logs
        self.anonymizer = anonymizer or Anonymizer(home / "kb" / "personas.yaml")

    def run(self, task: Task, task_dir: Path, kb: dict | None = None, attachments: list[dict] | None = None, **kwargs) -> StageResult:
        kb = select_stage_kb_context(self.name, kb or {})
        attachments = attachments or []
        policy = load_stage_policy(self.home, self.name)
        critic = PlannerCriticAgent()
        curator = PlannerCuratorAgent()
        change = PlannerChangeAgent()
        harness = StageHarness(StageSpec("planner", "02_plan", "initial_plan.json", "draft_plan.json", "02_plan.json", [TaskState.PLANNED]), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(_ctx):
            brief = load_json(task_dir, "01_triage/final_brief.json")
            required = [line.replace("required_section:", "").strip() for line in policy.core_prompt.splitlines() if "required_section:" in line]
            plan = PlannerPlan(
                objective=brief.get("goal", task.title),
                milestones=["Confirm scope", "Draft assets", "Review and publish"],
                dependencies=brief.get("constraints", [])[:3],
                approvals=["Task owner approval"],
                risks=brief.get("risks", [])[:3],
                mitigation=["Weekly risk checkpoint"],
                success_criteria=brief.get("success_criteria", [])[:3],
                open_questions=required,
            )
            return plan.to_dict()

        def update(_ctx, draft):
            plan = PlannerPlan.from_dict(draft)
            for q in ["deadline", "success criteria", "dependencies", "approvals"]:
                a = ask_multiline(self.io, f"Planning clarification for {q}")
                if a.strip():
                    plan.open_questions.append(f"{q}: {self.anonymizer.collect_from_text(a, self.io)[0]}")
            return plan.to_dict(), {"learning_summary": "Plan updated via HITL clarifications.", "decisions": plan.approvals, "resolved_unknowns": [], "remaining_unknowns": plan.open_questions}

        def post(ctx, initial, final):
            critic_eval = critic.evaluate(initial or {}, final, ctx.policy)
            delta_md, candidates_yaml = curator.curate(initial or {}, final, ctx.policy)
            return {
                "02_plan/plan_critic_eval.json": critic_eval,
                "02_plan/delta_learning.md": delta_md,
                "02_plan/learning_candidates.yaml": candidates_yaml,
                "02_plan/change_request.md": change.generate(task.task_id, critic_eval, {}, self.home, allow_history_write=ctx.run_mode_policy.allow_policy_history_write),
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post, **kwargs)
