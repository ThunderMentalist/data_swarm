"""Comms stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy, select_stage_kb_context
from data_swarm.orchestrator.hitl import comms_review
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.artifacts import load_json
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.comms.change import CommsChangeAgent
from data_swarm.stages.comms.critic import CommsCriticAgent
from data_swarm.stages.comms.curator import CommsCuratorAgent
from data_swarm.stages.comms.models import ChannelDraft, CommsPackage
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO


class CommsStage(AgenticStage):
    name = "comms"

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
        critic = CommsCriticAgent()
        curator = CommsCuratorAgent()
        change = CommsChangeAgent()
        harness = StageHarness(StageSpec("comms", "05_comms", "initial_drafts.json", "draft_comms.json", "final_comms.json", [TaskState.OUTREACH_PENDING_REVIEW, TaskState.AWAITING_REPLIES]), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(ctx):
            nav = load_json(task_dir, "04_navigation/04_navigation.json")
            stakeholders = load_json(task_dir, "03_stakeholders/03_stakeholders.json")
            audience = ", ".join([r.get("role", "stakeholder") for r in stakeholders.get("roles", [])[:2]]) or "stakeholders"
            forbidden = [line.replace("forbidden:", "").strip() for line in ctx.policy.core_prompt.splitlines() if line.startswith("forbidden:")]
            base = f"Task: {task.title}\nSequence: {', '.join(nav.get('outreach_sequence', []))}\nAudience: {audience}"
            if forbidden:
                base += f"\nAvoid: {', '.join(forbidden)}"
            return CommsPackage(channels=[
                ChannelDraft("email", audience, "inform", "confirm approval", base),
                ChannelDraft("teams", audience, "update", "ack receipt", f"Short update: {task.title}"),
            ]).to_dict()

        def update(_ctx, draft):
            pack = CommsPackage.from_dict(draft)
            reviewed = comms_review(self.io, {row.channel: row.draft for row in pack.channels})
            for row in pack.channels:
                row.draft = self.anonymizer.collect_from_text(reviewed[row.channel]["approved"], self.io)[0]
                row.approval_status = "approved"
            return pack.to_dict(), {"learning_summary": "Comms package reviewed and approved.", "decisions": [c.channel for c in pack.channels], "resolved_unknowns": [], "remaining_unknowns": []}

        def post(ctx, initial, final):
            critic_eval = critic.evaluate(initial or {}, final, ctx.policy)
            delta_md, candidates_yaml = curator.curate(initial or {}, final, ctx.policy)
            if ctx.memory_store and ctx.run_mode_policy.allow_memory_write:
                for row in final.get("channels", []):
                    if row.get("approval_status") == "approved":
                        ctx.memory_store.add_personal_preference(f"channel.{row.get('channel')}", row.get("draft", ""), task.task_id)
            return {
                "05_comms/comms_critic_eval.json": critic_eval,
                "05_comms/delta_learning.md": delta_md,
                "05_comms/learning_candidates.yaml": candidates_yaml,
                "05_comms/change_request.md": change.generate(task.task_id, critic_eval, {}, self.home, allow_history_write=ctx.run_mode_policy.allow_policy_history_write),
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post, **kwargs)
