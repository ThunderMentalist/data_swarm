"""Navigation stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy, select_stage_kb_context
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.artifacts import load_json
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stages.navigation.change import NavigationChangeAgent
from data_swarm.stages.navigation.critic import NavigationCriticAgent
from data_swarm.stages.navigation.curator import NavigationCuratorAgent
from data_swarm.stages.navigation.models import NavigationPlan
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO


class NavigationStage(AgenticStage):
    name = "navigation"

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
        critic = NavigationCriticAgent()
        curator = NavigationCuratorAgent()
        change = NavigationChangeAgent()
        harness = StageHarness(StageSpec("navigation", "04_navigation", "initial_navigation.json", "draft_navigation.json", "04_navigation.json", []), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(_ctx):
            stakeholders = load_json(task_dir, "03_stakeholders/03_stakeholders.json").get("roles", [])
            plan = load_json(task_dir, "02_plan/02_plan.json")
            order = [role.get("role", "stakeholder") for role in stakeholders] or ["Task Owner"]
            nav = NavigationPlan(
                outreach_sequence=order,
                rationale=["Sequence starts with high influence stakeholders"],
                gating_dependencies=plan.get("dependencies", []),
                political_risks=[r.get("notes", "alignment risk") for r in kb.get("politics_map", {}).get("relationships", [])[:2]],
                contingencies=["Escalate to sponsor if no response in 48h"],
                escalation_triggers=["No acknowledgement after 2 nudges"],
            )
            return nav.to_dict()

        def update(_ctx, draft):
            nav = NavigationPlan.from_dict(draft)
            a = ask_multiline(self.io, "Navigation clarification")
            if a.strip():
                nav.rationale.append(self.anonymizer.collect_from_text(a, self.io)[0])
            return nav.to_dict(), {"learning_summary": "Navigation sequence refined.", "decisions": nav.outreach_sequence, "resolved_unknowns": [], "remaining_unknowns": []}

        def post(ctx, initial, final):
            critic_eval = critic.evaluate(initial or {}, final, ctx.policy)
            delta_md, candidates_yaml = curator.curate(initial or {}, final, ctx.policy)
            if ctx.memory_store and ctx.run_mode_policy.allow_memory_write:
                for item in final.get("contingencies", [])[:2]:
                    ctx.memory_store.add_org_playbook("navigation", item, task.task_id)
            return {
                "04_navigation/navigation_critic_eval.json": critic_eval,
                "04_navigation/delta_learning.md": delta_md,
                "04_navigation/learning_candidates.yaml": candidates_yaml,
                "04_navigation/change_request.md": change.generate(task.task_id, critic_eval, {}, self.home, allow_history_write=ctx.run_mode_policy.allow_policy_history_write),
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post, **kwargs)
