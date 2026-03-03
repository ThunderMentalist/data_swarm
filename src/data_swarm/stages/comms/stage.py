"""Comms stage orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm import yaml_compat as yaml
from data_swarm.orchestrator.hitl import ask_yes_no, comms_review
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.comms.change import CommsChangeAgent
from data_swarm.stages.comms.concierge import CommsConciergeAgent
from data_swarm.stages.comms.critic import CommsCriticAgent
from data_swarm.stages.comms.curator import CommsCuratorAgent
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import UserIO


class CommsStage(AgenticStage):
    """Agentic comms stage with approval gate."""

    name = "comms"

    def __init__(self, config: dict, home: Path, io: UserIO, store: TaskStore, logs: LogStore) -> None:
        self.config = config
        self.home = home
        self.io = io
        self.store = store
        self.logs = logs

    def run(self, task: Task, task_dir: Path) -> StageResult:
        stage_dir = task_dir / "05_comms"
        stage_dir.mkdir(parents=True, exist_ok=True)

        final_payload_path = stage_dir / "final_comms.json"
        if final_payload_path.exists():
            return StageResult(True, task.state, ["05_comms/final_comms.json"])

        concierge = CommsConciergeAgent()
        critic = CommsCriticAgent()
        curator = CommsCuratorAgent()
        change = CommsChangeAgent()

        tone_profile_path = self.home / "tone_profile.md"
        tone_profile = tone_profile_path.read_text(encoding="utf-8") if tone_profile_path.exists() else "Diplomatic"
        draft_email = concierge.initial_email_draft(task.title, task.description, tone_profile)
        drafts = {
            "email": draft_email,
            "teams": "Short update: " + task.title,
            "talking_points": "- status\n- risks\n- asks",
            "meeting_brief": "Objective and agenda",
        }
        initial_path = stage_dir / "initial_drafts.json"
        history_path = stage_dir / "comms_history.jsonl"
        if not initial_path.exists():
            initial_path.write_text(json.dumps(drafts, indent=2), encoding="utf-8")
        if not history_path.exists():
            self._append_jsonl(history_path, concierge.snapshot(drafts))

        artifacts = ["05_comms/initial_drafts.json", "05_comms/comms_history.jsonl"]
        (stage_dir / "review_context.md").write_text("# Review Context\n\nGenerated from planning artifacts and task brief.", encoding="utf-8")
        artifacts.append("05_comms/review_context.md")

        reviewed = comms_review(self.io, drafts)
        approved_map = {channel: payload["approved"] for channel, payload in reviewed.items()}
        self._append_jsonl(history_path, concierge.snapshot(approved_map))

        if not ask_yes_no(self.io, "Approve this comms package to proceed?", default_no=True):
            target = TaskState.REPLANNING if task.state in {
                TaskState.PLANNED,
                TaskState.OUTREACH_PENDING_REVIEW,
                TaskState.AWAITING_REPLIES,
            } else TaskState.NEEDS_CLARIFICATION
            if task.state != target:
                apply_transition(task, target, "comms package not approved", ["05_comms/comms_history.jsonl"], self.store, self.logs, self.name)
            return StageResult(False, task.state, sorted(set(artifacts)))

        for channel, payload in reviewed.items():
            (stage_dir / f"{channel}_draft.md").write_text(payload["draft"], encoding="utf-8")
            (stage_dir / f"{channel}_approved.md").write_text(payload["approved"], encoding="utf-8")
        final_payload_path.write_text(json.dumps(approved_map, indent=2), encoding="utf-8")
        artifacts.extend([
            "05_comms/email_draft.md",
            "05_comms/email_approved.md",
            "05_comms/teams_draft.md",
            "05_comms/teams_approved.md",
            "05_comms/talking_points_draft.md",
            "05_comms/talking_points_approved.md",
            "05_comms/meeting_brief_draft.md",
            "05_comms/meeting_brief_approved.md",
            "05_comms/final_comms.json",
        ])

        apply_transition(task, TaskState.OUTREACH_PENDING_REVIEW, "comms drafts generated and reviewed", ["05_comms/review_context.md"], self.store, self.logs, self.name)
        apply_transition(task, TaskState.AWAITING_REPLIES, "approved comms ready for outreach", ["05_comms/email_approved.md"], self.store, self.logs, self.name)

        critic_eval = critic.evaluate(drafts, approved_map)
        (stage_dir / "comms_critic_eval.json").write_text(json.dumps(critic_eval, indent=2), encoding="utf-8")
        delta_md, candidates_yaml = curator.curate(drafts, approved_map)
        (stage_dir / "delta_learning.md").write_text(delta_md, encoding="utf-8")
        (stage_dir / "learning_candidates.yaml").write_text(candidates_yaml, encoding="utf-8")
        change_request = change.generate(task.task_id, critic_eval, yaml.safe_load(candidates_yaml) or {}, self.home)
        (stage_dir / "change_request.md").write_text(change_request, encoding="utf-8")
        artifacts.extend([
            "05_comms/comms_critic_eval.json",
            "05_comms/delta_learning.md",
            "05_comms/learning_candidates.yaml",
            "05_comms/change_request.md",
        ])
        return StageResult(True, task.state, sorted(set(artifacts)))

    @staticmethod
    def _append_jsonl(path: Path, payload: dict) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
