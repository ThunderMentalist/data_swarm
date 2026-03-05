"""Consent-driven triage stage orchestration."""

from __future__ import annotations

from pathlib import Path

from data_swarm.kb import load_stage_policy
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
from data_swarm.tools.io import UserIO, ConsoleIO


class TriageStage(AgenticStage):
    """Agentic triage stage with explicit approval gate."""

    name = "triage"

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
        concierge = TriageConciergeAgent(policy_pack=policy)
        critic = TriageCriticAgent()
        curator = TriageCuratorAgent()
        change = TriageChangeAgent()
        harness = StageHarness(
            StageSpec(
                stage_key="triage",
                stage_dir="01_triage",
                initial_name="initial_brief.json",
                draft_name="draft_brief.json",
                final_name="final_brief.json",
                expected_transitions_on_approval=[TaskState.TRIAGED],
                non_approval_target=lambda _task: TaskState.NEEDS_CLARIFICATION,
            ),
            io=self.io,
            store=self.store,
            logs=self.logs,
            anonymizer=self.anonymizer,
        )

        def make_initial(ctx):
            intake_path = ctx.task_dir / "00_intake" / "00_intake.md"
            intake_text = intake_path.read_text(encoding="utf-8") if intake_path.exists() else ctx.task.description
            sanitized, _ = self.anonymizer.collect_from_text(intake_text, self.io)
            brief = concierge.propose_initial_brief(sanitized)
            brief.inputs_available.extend([f"{x['filename']} ({x['sha256'][:8]})" for x in ctx.attachments])
            patch_path = ctx.task_dir / "06_feedback" / "triage_update_patch.json"
            if patch_path.exists():
                patch = __import__("json").loads(patch_path.read_text(encoding="utf-8"))
                brief.constraints.extend(patch.get("clarified_constraints", []))
                brief.context = (brief.context + "\nFeedback patch facts: " + "; ".join(patch.get("new_facts", []))).strip()
            return brief.to_dict()

        def update_draft(ctx, draft):
            current = TaskBrief.from_dict(draft)
            qa = []
            if ctx.attachments:
                confirm = ask_multiline(ctx.io, "Confirm which attachments should be relied on (or leave blank)")
                if confirm:
                    current.inputs_available.append(confirm)
            for question in concierge.next_questions(current):
                answer = ask_multiline(ctx.io, f"Clarification: {question}")
                sanitized, _ = self.anonymizer.collect_from_text(answer, self.io)
                qa.append((question, sanitized))
            updated = concierge.apply_answers(current, qa)
            ctx.io.tell("Current brief:\n" + concierge.format_brief(updated))
            return updated.to_dict(), {
                "learning_summary": "Brief refined with clarified goal, constraints, and known inputs.",
                "decisions": ["Proposed task_type recorded for confirmation"],
                "resolved_unknowns": [q for q, _ in qa if _],
                "remaining_unknowns": [],
            }

        def render_final(_ctx, draft):
            return draft

        def post(_ctx, initial, final):
            init = TaskBrief.from_dict(initial or TaskBrief.empty().to_dict())
            fin = TaskBrief.from_dict(final)
            critic_eval = critic.evaluate(init, fin, [])
            delta_md, candidates_yaml = curator.curate(init, fin)
            change_request = change.generate(task.task_id, critic_eval, {}, self.home)
            return {
                "01_triage/triage_critic_eval.json": critic_eval,
                "01_triage/delta_learning.md": delta_md,
                "01_triage/learning_candidates.yaml": candidates_yaml,
                "01_triage/change_request.md": change_request,
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update_draft, render_final, post)
