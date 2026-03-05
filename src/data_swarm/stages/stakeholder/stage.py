"""Stakeholder stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stages.stakeholder.change import StakeholderChangeAgent
from data_swarm.stages.stakeholder.concierge import StakeholderConciergeAgent
from data_swarm.stages.stakeholder.critic import StakeholderCriticAgent
from data_swarm.stages.stakeholder.curator import StakeholderCuratorAgent
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO, ConsoleIO


class StakeholderStage(AgenticStage):
    name = "stakeholder"

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
        concierge = StakeholderConciergeAgent()
        critic = StakeholderCriticAgent()
        curator = StakeholderCuratorAgent()
        change = StakeholderChangeAgent()
        harness = StageHarness(StageSpec("stakeholder", "03_stakeholders", "initial_stakeholders.yaml", "draft_stakeholders.yaml", "03_stakeholders.yaml", [], lambda _t: TaskState.NEEDS_CLARIFICATION), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(_ctx):
            return concierge.initial_map()

        def update(_ctx, draft):
            edited = ask_multiline(self.io, "Paste revised stakeholder YAML; END to finish; empty keeps current")
            updated = self.anonymizer.collect_from_text(edited, self.io)[0] + "\n" if edited.strip() else draft
            self.io.tell("Current stakeholder map:\n" + updated)
            return updated, {"learning_summary": "Stakeholder map refined and anonymized.", "decisions": [], "resolved_unknowns": [], "remaining_unknowns": []}

        def post(_ctx, initial, final):
            critic_eval = critic.evaluate(initial or "", final)
            delta_md, candidates_yaml = curator.curate(initial or "", final)
            return {
                "03_stakeholders/stakeholder_critic_eval.json": critic_eval,
                "03_stakeholders/delta_learning.md": delta_md,
                "03_stakeholders/learning_candidates.yaml": candidates_yaml,
                "03_stakeholders/change_request.md": change.generate(task.task_id, critic_eval, {}, self.home),
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post)
