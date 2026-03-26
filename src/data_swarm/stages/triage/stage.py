"""Consent-driven triage stage orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm.kb import load_stage_policy, select_stage_kb_context
from data_swarm.llm import LLMProfile
from data_swarm.orchestrator.execution_context import ExecutionContext
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stages.triage.change import TriageChangeAgent
from data_swarm.stages.triage.concierge import TriageConciergeAgent
from data_swarm.stages.triage.critic import TriageCriticAgent
from data_swarm.stages.triage.curator import TriageCuratorAgent
from data_swarm.stages.triage.models import TaskBrief
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.attachments import ingest_selected_attachments
from data_swarm.tools.io import UserIO


class TriageStage(AgenticStage):
    name = "triage"

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
            execution_context.try_llm_profile("triage.concierge") if execution_context else None
        )
        self.critic_profile: LLMProfile | None = (
            execution_context.try_llm_profile("triage.critic", fallback="triage.concierge") if execution_context else None
        )

    def run(self, task: Task, task_dir: Path, kb: dict | None = None, attachments: list[dict] | None = None, **kwargs) -> StageResult:
        kb = select_stage_kb_context(self.name, kb or {})
        attachments = attachments or []
        policy = load_stage_policy(self.home, self.name)
        concierge = TriageConciergeAgent(policy_pack=policy)
        critic = TriageCriticAgent()
        curator = TriageCuratorAgent()
        change = TriageChangeAgent()
        harness = StageHarness(
            StageSpec(stage_key="triage", stage_dir="01_triage", initial_name="initial_brief.json", draft_name="draft_brief.json", final_name="final_brief.json", expected_transitions_on_approval=[TaskState.TRIAGED]),
            io=self.io,
            store=self.store,
            logs=self.logs,
            anonymizer=self.anonymizer,
        )

        def make_initial(ctx):
            refined_path = ctx.task_dir / "00_intake" / "refined_task.md"
            raw_path = ctx.task_dir / "00_intake" / "raw_input.md"
            intake_text = refined_path.read_text(encoding="utf-8") if refined_path.exists() else (raw_path.read_text(encoding="utf-8") if raw_path.exists() else ctx.task.description)
            sanitized, _ = self.anonymizer.collect_from_text(intake_text, self.io)
            brief = concierge.propose_initial_brief(sanitized)
            brief.inputs_available.extend([f"{x['filename']} ({x['sha256'][:8]})" for x in ctx.attachments])
            if ctx.memory_store:
                prefs = ctx.memory_store.get_personal_preferences("channel.")
                if prefs:
                    brief.readiness_hints.append(f"Known comms prefs: {', '.join(list(prefs.keys())[:3])}")
            return brief.to_dict()

        def update_draft(ctx, draft):
            current = TaskBrief.from_dict(draft)
            qa = []
            for question in concierge.next_questions(current):
                answer = ask_multiline(ctx.io, f"Clarification: {question}")
                sanitized, _ = self.anonymizer.collect_from_text(answer, self.io)
                qa.append((question, sanitized))
            updated = concierge.apply_answers(current, qa)
            if not updated.goal:
                updated.goal = task.title
            if not updated.deliverable:
                updated.deliverable = "Written recommendation"
            ctx.io.tell("Current brief:\n" + concierge.format_brief(updated))
            return updated.to_dict(), {"learning_summary": "Brief refined with clarified goal, constraints, and inputs.", "decisions": ["Proposed task_type recorded for confirmation"], "resolved_unknowns": [q for q, a in qa if a], "remaining_unknowns": []}

        def render_final(_ctx, draft):
            return draft

        def post(ctx, initial, final):
            init = TaskBrief.from_dict(initial or TaskBrief.empty().to_dict())
            fin = TaskBrief.from_dict(final)
            inv, summary, extracted = ingest_selected_attachments(
                ctx.task_dir,
                ctx.attachments,
                fin.requested_attachments,
                self.config.get("attachment_ingest", {}),
                enabled=ctx.run_mode_policy.attachment_ingest_enabled,
            )
            extracted_payload = {
                "requested_files": fin.requested_attachments,
                "inventory": inv,
                "summary": summary,
                "extracted_text": extracted,
            }
            critic_eval = critic.evaluate(init, fin, ctx.policy)
            delta_md, candidates_yaml = curator.curate(init, fin, ctx.policy)
            change_request = change.generate(task.task_id, critic_eval, {}, self.home, allow_history_write=ctx.run_mode_policy.allow_policy_history_write)
            return {
                "01_triage/triage_critic_eval.json": critic_eval,
                "01_triage/delta_learning.md": delta_md,
                "01_triage/learning_candidates.yaml": candidates_yaml,
                "01_triage/change_request.md": change_request,
                "01_triage/requested_attachment_extraction.json": extracted_payload,
                f"01_triage/cycle_{task.cycle_id:04d}/requested_attachment_extraction.json": extracted_payload,
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update_draft, render_final, post, **kwargs)
