"""Triage change request agent and repetition detection."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from data_swarm.stages.policy_store import StagePolicyStore


class TriageChangeAgent:
    name = "Triage Change Agent"

    def generate(self, task_id: str, critic_eval: dict, curator_candidates: dict, home: Path, allow_history_write: bool = True) -> str:
        store = StagePolicyStore(home, "triage")
        store.ensure_scaffold()
        suggestions = critic_eval.get("suggestions", [])
        suggestion_keys = [s.get("suggestion_key") or s.get("title", "").strip().lower().replace(" ", "_") for s in suggestions]
        repetition_index = store.update_repetition_index(suggestion_keys) if allow_history_write else {k: 1 for k in suggestion_keys}
        lines = ["# Triage Change Request", "", "## Suggested changes"]
        for suggestion, key in zip(suggestions, suggestion_keys):
            lines.extend([f"- **{suggestion.get('title', 'Untitled suggestion')}**", f"  - Rationale: {suggestion.get('rationale', '')}", f"  - Evidence: {suggestion.get('evidence', '')}"])
            count = repetition_index.get(key, 1)
            if count > 1:
                lines.append(f"  - Repetition signal: seen {count} times; becoming repetitive.")
        lines.extend(["", "## Curator candidates", json.dumps(curator_candidates, indent=2)])
        if allow_history_write:
            store.append_change_record({"timestamp": datetime.now(timezone.utc).isoformat(), "task_id": task_id, "suggestion_keys": suggestion_keys, "titles": [s.get("title", "") for s in suggestions]})
        return "\n".join(lines).rstrip() + "\n"
