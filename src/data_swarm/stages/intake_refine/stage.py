"""Intake refine stage."""

from __future__ import annotations

import hashlib
from pathlib import Path

from data_swarm.kb import load_stage_policy
from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.harness import StageHarness, StageSpec
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.attachments import ingest_attachments
from data_swarm.tools.io import UserIO


class IntakeRefineStage(AgenticStage):
    name = "intake_refine"

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
        harness = StageHarness(StageSpec("intake_refine", "00_intake", "initial_refined_task.md", "draft_refined_task.md", "refined_task.md", []), self.io, self.store, self.logs, self.anonymizer)

        def make_initial(ctx):
            raw = (ctx.task_dir / "00_intake" / "raw_input.md")
            text = raw.read_text(encoding="utf-8") if raw.exists() else ctx.task.description
            return f"## Objective\n\n{text}\n"

        def update(_ctx, draft):
            notes = ask_multiline(self.io, "Add intake refinement notes (or END)")
            updated = draft + ("\n\n" + notes if notes else "")
            return updated, {"learning_summary": "Intake refined.", "decisions": [], "resolved_unknowns": [], "remaining_unknowns": []}

        def post(ctx, _initial, final):
            cfg = self.config.get("attachment_ingest", {})
            inventory, summary, _ = ingest_attachments(ctx.task_dir, ctx.attachments, cfg)
            digest = hashlib.sha256(final.encode("utf-8")).hexdigest()
            task.refined_task_digest = digest
            task.refined_task_path = "00_intake/refined_task.md"
            task.raw_input_path = "00_intake/raw_input.md"
            task.refined_context_path = "00_intake/context.yaml"
            task.attachments_summary_path = "00_intake/attachments_summary.md"
            self.store.save(task)
            return {
                f"00_intake/cycle_{task.cycle_id:04d}/context.yaml": "objective: refined\n",
                f"00_intake/cycle_{task.cycle_id:04d}/attachments_inventory.json": inventory,
                f"00_intake/cycle_{task.cycle_id:04d}/attachments_summary.md": summary,
                "00_intake/refined_task.md": final,
                "00_intake/context.yaml": "objective: refined\n",
                "00_intake/attachments_summary.md": summary,
            }

        return harness.run(task, task_dir, kb, policy, attachments, make_initial, update, lambda _c, d: d, post)
