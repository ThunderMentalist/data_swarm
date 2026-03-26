"""Reaction stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy, select_stage_kb_context
from data_swarm.llm import LLMProfile
from data_swarm.orchestrator.execution_context import ExecutionContext
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.artifacts import load_stage_inputs
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stages.reaction.models import ReactionAnalysis
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import UserIO


class ReactionStage(AgenticStage):
    """Reply-ingestion stage that produces triage update patches + readiness hints."""

    name = "reaction"

    def __init__(
        self,
        config: dict,
        home: Path,
        io: UserIO,
        store: TaskStore,
        logs: LogStore,
        anonymizer: Anonymizer | None = None,
        execution_context: ExecutionContext | None = None,
    ) -> None:
        self.config = config
        self.home = home
        self.io = io
        self.store = store
        self.logs = logs
        self.anonymizer = anonymizer or Anonymizer(home / "kb" / "personas.yaml")
        self.execution_context = execution_context
        self.concierge_profile: LLMProfile | None = (
            execution_context.try_llm_profile("reaction.concierge") if execution_context else None
        )

    def run(self, task: Task, task_dir: Path, kb: dict | None = None, attachments: list[dict] | None = None, **kwargs) -> StageResult:
        kb = select_stage_kb_context(self.name, kb or {})
        attachments = attachments or []
        policy = load_stage_policy(self.home, self.name)
        harness = StageHarness(StageSpec("reaction", "06_reaction", "initial_reaction.json", "draft_reaction.json", "final_reaction.json", []), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(_ctx):
            return ReactionAnalysis(summary="").to_dict()

        def update(ctx, draft):
            current = ReactionAnalysis.from_dict(draft)
            text = ask_multiline(self.io, "Paste reaction summary from external interactions")
            sanitized, _ = self.anonymizer.collect_from_text(text, self.io)
            sentences = [s.strip() for s in sanitized.replace("\n", " ").split(".") if s.strip()]
            current.summary = sanitized
            current.new_facts = [s for s in sentences if any(k in s.lower() for k in ["is", "are", "observed", "confirmed"])][:5]
            current.blockers = [s for s in sentences if any(k in s.lower() for k in ["blocked", "risk", "issue", "stuck"])][:5]
            current.commitments = [s for s in sentences if any(k in s.lower() for k in ["will", "commit", "by "])][:5]
            current.clarified_constraints = current.blockers[:]
            current.open_questions = [s for s in sentences if "?" in s or "question" in s.lower()][:5]
            upstream = load_stage_inputs(task_dir)
            comms_done = bool(upstream.get("comms"))
            current.impact_assessment = "Material scope impact" if current.blockers else "No critical impact"
            current.readiness_recommendation = "REPLANNING" if current.blockers else ("READY_TO_DELIVER" if comms_done and current.open_questions == [] else "AWAITING_REPLIES")
            current.readiness_reason = "Blockers detected" if current.blockers else "No blockers and outreach complete"
            return current.to_dict(), {"learning_summary": "External reactions captured and structured for replanning/readiness.", "decisions": current.commitments, "resolved_unknowns": current.new_facts, "remaining_unknowns": current.open_questions}

        def post(ctx, _initial, final):
            reaction = ReactionAnalysis.from_dict(final)
            patch = {
                "new_facts": reaction.new_facts,
                "clarified_constraints": reaction.clarified_constraints,
                "updated_stakeholders": [],
                "preference_signals": reaction.commitments,
                "recommended_brief_updates": reaction.new_facts,
                "suggested_task_type_update": "",
            }
            if ctx.memory_store and ctx.run_mode_policy.allow_memory_write and reaction.commitments:
                ctx.memory_store.add_org_playbook("reaction", reaction.commitments[0], task.task_id)
            return {f"06_reaction/cycle_{task.cycle_id:04d}/triage_update_patch.json": patch, "06_reaction/triage_update_patch.json": patch}

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post, **kwargs)
