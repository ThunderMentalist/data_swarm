"""Stakeholder stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy, select_stage_kb_context
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.artifacts import load_json
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stages.stakeholder.change import StakeholderChangeAgent
from data_swarm.stages.stakeholder.critic import StakeholderCriticAgent
from data_swarm.stages.stakeholder.curator import StakeholderCuratorAgent
from data_swarm.stages.stakeholder.models import StakeholderMap, StakeholderRole
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO


class StakeholderStage(AgenticStage):
    name = "stakeholder"

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
        critic = StakeholderCriticAgent()
        curator = StakeholderCuratorAgent()
        change = StakeholderChangeAgent()
        harness = StageHarness(StageSpec("stakeholder", "03_stakeholders", "initial_stakeholders.json", "draft_stakeholders.json", "03_stakeholders.json", []), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(ctx):
            brief = load_json(task_dir, "01_triage/final_brief.json")
            plan = load_json(task_dir, "02_plan/02_plan.json")
            roles = [StakeholderRole(role=r.get("role_token", "Task Owner"), influence="medium", interest="high", decision_rights="consult", stance="neutral", engagement_plan="weekly async update", escalation_path="manager") for r in kb.get("role_registry", {}).get("roles", [])[:3]]
            if not roles:
                roles = [StakeholderRole(role="Task Owner", influence="high", interest="high", decision_rights="approve", stance="supportive", engagement_plan="daily sync", escalation_path="program lead")]
            roles[0].engagement_plan = f"align on objective: {brief.get('goal', task.title)}"
            if plan.get("approvals"):
                roles[0].decision_rights = ",".join(plan.get("approvals", [])[:2])
            return StakeholderMap(roles=roles).to_dict()

        def update(_ctx, draft):
            edited = ask_multiline(self.io, "Optional stakeholder notes")
            data = StakeholderMap.from_dict(draft)
            if edited.strip() and data.roles:
                data.roles[0].engagement_plan = self.anonymizer.collect_from_text(edited, self.io)[0]
            return data.to_dict(), {"learning_summary": "Stakeholder map refined and anonymized.", "decisions": [r.role for r in data.roles], "resolved_unknowns": [], "remaining_unknowns": []}

        def post(ctx, initial, final):
            critic_eval = critic.evaluate(initial or {}, final, ctx.policy)
            delta_md, candidates_yaml = curator.curate(initial or {}, final, ctx.policy)
            if ctx.memory_store and ctx.run_mode_policy.allow_memory_write:
                for role in final.get("roles", []):
                    ctx.memory_store.add_role_note(role.get("role", "unknown"), role.get("engagement_plan", ""), task.task_id)
            return {
                "03_stakeholders/stakeholder_critic_eval.json": critic_eval,
                "03_stakeholders/delta_learning.md": delta_md,
                "03_stakeholders/learning_candidates.yaml": candidates_yaml,
                "03_stakeholders/change_request.md": change.generate(task.task_id, critic_eval, {}, self.home, allow_history_write=ctx.run_mode_policy.allow_policy_history_write),
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post, **kwargs)
