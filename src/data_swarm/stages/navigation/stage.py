"""Navigation stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stages.navigation.change import NavigationChangeAgent
from data_swarm.stages.navigation.concierge import NavigationConciergeAgent
from data_swarm.stages.navigation.critic import NavigationCriticAgent
from data_swarm.stages.navigation.curator import NavigationCuratorAgent
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO, ConsoleIO


class NavigationStage(AgenticStage):
    name = "navigation"

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
        concierge = NavigationConciergeAgent()
        critic = NavigationCriticAgent()
        curator = NavigationCuratorAgent()
        change = NavigationChangeAgent()
        harness = StageHarness(StageSpec("navigation", "04_navigation", "initial_navigation.md", "draft_navigation.md", "04_navigation.md", [TaskState.PLANNED], lambda t: TaskState.REPLANNING if t.state in {TaskState.PLANNED, TaskState.OUTREACH_PENDING_REVIEW, TaskState.AWAITING_REPLIES} else TaskState.NEEDS_CLARIFICATION), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(_ctx):
            return concierge.initial_plan()

        def update(_ctx, draft):
            notes = []
            for q in concierge.next_questions():
                a = ask_multiline(self.io, f"Navigation clarification: {q}")
                notes.append(f"- {q} -> {self.anonymizer.collect_from_text(a, self.io)[0] or 'No input'}")
            edited = ask_multiline(self.io, "Paste revised navigation section or notes; END to finish; empty keeps generated draft")
            updated = concierge.apply_edits(draft, "\n".join(notes + ([edited] if edited else [])))
            self.io.tell("Current navigation plan:\n" + updated)
            return updated, {"learning_summary": "Navigation sequence refined.", "decisions": [], "resolved_unknowns": [], "remaining_unknowns": []}

        def post(_ctx, initial, final):
            critic_eval = critic.evaluate(initial or "", final)
            delta_md, candidates_yaml = curator.curate(initial or "", final)
            return {
                "04_navigation/navigation_critic_eval.json": critic_eval,
                "04_navigation/delta_learning.md": delta_md,
                "04_navigation/learning_candidates.yaml": candidates_yaml,
                "04_navigation/change_request.md": change.generate(task.task_id, critic_eval, {}, self.home),
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post)
