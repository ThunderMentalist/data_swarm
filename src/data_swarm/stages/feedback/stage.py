"""Feedback stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO, ConsoleIO


class FeedbackStage(AgenticStage):
    """Feedback stage that produces triage update patches."""

    name = "feedback"

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
        harness = StageHarness(StageSpec("feedback", "06_feedback", "initial_feedback.json", "draft_feedback.json", "final_feedback.json", [], lambda _t: TaskState.REPLANNING), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(_ctx):
            return {"summary": "", "facts": [], "decisions": [], "open_questions": [], "commitments": [], "blockers": []}

        def update(_ctx, draft):
            text = ask_multiline(self.io, "Paste feedback summary from external interactions")
            sanitized, _ = self.anonymizer.collect_from_text(text, self.io)
            sentences = [s.strip() for s in sanitized.replace("\n", " ").split(".") if s.strip()]
            draft["summary"] = sanitized
            draft["facts"] = [s for s in sentences if any(k in s.lower() for k in ["is", "are", "observed"])][:5]
            draft["decisions"] = [s for s in sentences if any(k in s.lower() for k in ["decided", "approved", "chose"])][:5]
            draft["open_questions"] = [s for s in sentences if "?" in s or "question" in s.lower()][:5]
            draft["commitments"] = [s for s in sentences if any(k in s.lower() for k in ["will", "commit", "by "])][:5]
            draft["blockers"] = [s for s in sentences if any(k in s.lower() for k in ["blocked", "risk", "issue"])][:5]
            return draft, {"learning_summary": "External feedback captured and structured for next triage cycle.", "decisions": draft["decisions"], "resolved_unknowns": draft["facts"], "remaining_unknowns": draft["open_questions"]}

        def post(_ctx, _initial, final):
            patch = {
                "new_facts": final.get("facts", []),
                "clarified_constraints": final.get("blockers", []),
                "updated_stakeholders": [],
                "preference_signals": final.get("commitments", []),
                "recommended_brief_updates": final.get("facts", []),
                "suggested_task_type_update": "",
            }
            return {"06_feedback/triage_update_patch.json": patch}

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post)
