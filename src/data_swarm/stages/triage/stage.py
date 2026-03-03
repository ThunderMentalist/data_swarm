"""Consent-driven triage stage orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from data_swarm import yaml_compat as yaml
from data_swarm.orchestrator.hitl import ask_multiline, ask_yes_no
from data_swarm.orchestrator.task_models import Task, TaskState
from data_swarm.orchestrator.transitions import apply_transition
from data_swarm.stages.base import AgenticStage, StageResult
from data_swarm.stages.triage.change import TriageChangeAgent
from data_swarm.stages.triage.concierge import TriageConciergeAgent
from data_swarm.stages.triage.critic import TriageCriticAgent
from data_swarm.stages.triage.curator import TriageCuratorAgent
from data_swarm.stages.triage.models import TaskBrief
from data_swarm.stages.triage.policy import load_policy_pack
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import UserIO
from data_swarm.tools.redaction import redact_identifiers


class TriageStage(AgenticStage):
    """Agentic triage stage with explicit approval gate."""

    name = "triage"

    def __init__(
        self,
        config: dict,
        home: Path,
        io: UserIO,
        store: TaskStore,
        logs: LogStore,
    ) -> None:
        self.config = config
        self.home = home
        self.io = io
        self.store = store
        self.logs = logs

    def run(self, task: Task, task_dir: Path) -> StageResult:
        """Run triage stage for task and return stage result."""
        triage_dir = task_dir / "01_triage"
        triage_dir.mkdir(parents=True, exist_ok=True)

        final_brief_path = triage_dir / "final_brief.json"
        if final_brief_path.exists():
            return StageResult(approved=True, artifacts_written=["01_triage/final_brief.json"])

        intake_text = self._load_intake_text(task, task_dir)
        initial_input = redact_identifiers(intake_text)

        policy_pack = load_policy_pack(self.home)
        concierge = TriageConciergeAgent(policy_pack=policy_pack)
        critic = TriageCriticAgent()
        curator = TriageCuratorAgent()
        change_agent = TriageChangeAgent()

        initial_brief_path = triage_dir / "initial_brief.json"
        brief_history_path = triage_dir / "brief_history.jsonl"
        clarification_log_path = triage_dir / "clarification_log.jsonl"

        if brief_history_path.exists():
            current_brief = self._load_last_brief(brief_history_path)
        else:
            current_brief = concierge.propose_initial_brief(initial_input)

        artifacts_written: list[str] = []
        if not initial_brief_path.exists():
            self._write_json(initial_brief_path, current_brief.to_dict())
            artifacts_written.append("01_triage/initial_brief.json")

        if not brief_history_path.exists():
            self._append_jsonl(brief_history_path, self._brief_snapshot(current_brief))
            artifacts_written.append("01_triage/brief_history.jsonl")

        initial_brief = TaskBrief.from_dict(json.loads(initial_brief_path.read_text(encoding="utf-8")))

        while True:
            questions = concierge.next_questions(current_brief)
            qa_round: list[tuple[str, str]] = []
            for question in questions:
                answer = ask_multiline(self.io, f"Clarification: {question}")
                answer_sanitized = redact_identifiers(answer)
                qa_round.append((question, answer_sanitized))
                self._append_jsonl(
                    clarification_log_path,
                    {
                        "timestamp": _utc_now(),
                        "question": question,
                        "answer": answer_sanitized,
                        "edit_summary": "captured clarification answer",
                    },
                )
            artifacts_written.append("01_triage/clarification_log.jsonl")

            current_brief = concierge.apply_answers(current_brief, qa_round)
            self._append_jsonl(brief_history_path, self._brief_snapshot(current_brief))
            self.io.tell("Current brief:\n" + concierge.format_brief(current_brief))

            approved = ask_yes_no(self.io, "Approve this brief to proceed?", default_no=True)
            if approved:
                break

            if task.state != TaskState.NEEDS_CLARIFICATION:
                apply_transition(
                    task,
                    TaskState.NEEDS_CLARIFICATION,
                    "triage brief not approved",
                    ["01_triage/brief_history.jsonl"],
                    self.store,
                    self.logs,
                    self.name,
                )
            return StageResult(approved=False, artifacts_written=sorted(set(artifacts_written)))

        self._write_json(final_brief_path, current_brief.to_dict())
        artifacts_written.append("01_triage/final_brief.json")

        clarification_tail = self._read_jsonl(clarification_log_path)[-10:] if clarification_log_path.exists() else []
        critic_eval = critic.evaluate(initial_brief, current_brief, clarification_tail)
        critic_path = triage_dir / "triage_critic_eval.json"
        self._write_json(critic_path, critic_eval)
        artifacts_written.append("01_triage/triage_critic_eval.json")

        delta_learning, candidates_yaml = curator.curate(initial_brief, current_brief)
        delta_path = triage_dir / "delta_learning.md"
        delta_path.write_text(delta_learning, encoding="utf-8")
        artifacts_written.append("01_triage/delta_learning.md")

        candidates_path = triage_dir / "learning_candidates.yaml"
        candidates_path.write_text(candidates_yaml, encoding="utf-8")
        artifacts_written.append("01_triage/learning_candidates.yaml")
        candidates_data = yaml.safe_load(candidates_yaml) or {}

        change_request = change_agent.generate(task.task_id, critic_eval, candidates_data, self.home)
        change_path = triage_dir / "change_request.md"
        change_path.write_text(change_request, encoding="utf-8")
        artifacts_written.append("01_triage/change_request.md")

        self.io.tell(
            "Change Request available: "
            f"{change_path} (optional to review; nothing auto-applied)"
        )
        return StageResult(approved=True, artifacts_written=sorted(set(artifacts_written)))

    def _load_intake_text(self, task: Task, task_dir: Path) -> str:
        intake_path = task_dir / "00_intake" / "00_intake.md"
        if intake_path.exists():
            return intake_path.read_text(encoding="utf-8")
        return task.description

    def _load_last_brief(self, brief_history_path: Path) -> TaskBrief:
        lines = brief_history_path.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            if not line.strip():
                continue
            payload = json.loads(line)
            snapshot = payload.get("brief_snapshot", {})
            return TaskBrief.from_dict(snapshot)
        return TaskBrief.empty()

    def _append_jsonl(self, path: Path, payload: dict) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _brief_snapshot(self, brief: TaskBrief) -> dict:
        return {"timestamp": _utc_now(), "brief_snapshot": brief.to_dict()}

    def _read_jsonl(self, path: Path) -> list[dict]:
        rows: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
