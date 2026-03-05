"""Comms stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy
from data_swarm.orchestrator.hitl import comms_review
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.comms.change import CommsChangeAgent
from data_swarm.stages.comms.concierge import CommsConciergeAgent
from data_swarm.stages.comms.critic import CommsCriticAgent
from data_swarm.stages.comms.curator import CommsCuratorAgent
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO, ConsoleIO


class CommsStage(AgenticStage):
    name = "comms"

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
        concierge = CommsConciergeAgent()
        critic = CommsCriticAgent()
        curator = CommsCuratorAgent()
        change = CommsChangeAgent()
        harness = StageHarness(StageSpec("comms", "05_comms", "initial_drafts.json", "draft_comms.json", "final_comms.json", [TaskState.OUTREACH_PENDING_REVIEW, TaskState.AWAITING_REPLIES], lambda t: TaskState.REPLANNING if t.state in {TaskState.PLANNED, TaskState.OUTREACH_PENDING_REVIEW, TaskState.AWAITING_REPLIES} else TaskState.NEEDS_CLARIFICATION), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(_ctx):
            tone_path = self.home / "tone_profile.md"
            tone = tone_path.read_text(encoding="utf-8") if tone_path.exists() else "Diplomatic"
            return {
                "email": concierge.initial_email_draft(task.title, task.description, tone),
                "teams": f"Short update: {task.title}",
                "talking_points": "- status\n- risks\n- asks",
                "meeting_brief": "Objective and agenda",
            }

        def update(_ctx, draft):
            reviewed = comms_review(self.io, draft)
            approved = {k: self.anonymizer.collect_from_text(v["approved"], self.io)[0] for k, v in reviewed.items()}
            return approved, {"learning_summary": "Comms package reviewed and approved copy drafted.", "decisions": list(approved.keys()), "resolved_unknowns": [], "remaining_unknowns": []}

        def post(_ctx, initial, final):
            critic_eval = critic.evaluate(initial or {}, final)
            delta_md, candidates_yaml = curator.curate(initial or {}, final)
            return {
                "05_comms/comms_critic_eval.json": critic_eval,
                "05_comms/delta_learning.md": delta_md,
                "05_comms/learning_candidates.yaml": candidates_yaml,
                "05_comms/change_request.md": change.generate(task.task_id, critic_eval, {}, self.home),
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post)
