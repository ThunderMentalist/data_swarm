"""Stakeholder change request agent."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from data_swarm.stages.policy_store import StagePolicyStore


class StakeholderChangeAgent:
    """Stakeholder Change Agent."""

    name = "Stakeholder Change Agent"

    def generate(self, task_id: str, critic_eval: dict, curator_candidates: dict, home: Path) -> str:
        """Generate change request markdown with repetition signals."""
        store = StagePolicyStore(home, "stakeholder")
        store.ensure_scaffold()
        suggestions = critic_eval.get("suggestions", [])
        keys = [s.get("suggestion_key", "stakeholder_suggestion") for s in suggestions]
        counts = store.update_repetition_index(keys)
        lines = ["# Stakeholder Change Request", "", "## Suggested changes"]
        for suggestion, key in zip(suggestions, keys):
            lines.append(f"- **{suggestion.get('title', 'Untitled suggestion')}**")
            lines.append(f"  - Rationale: {suggestion.get('rationale', '')}")
            lines.append(f"  - Evidence: {suggestion.get('evidence', '')}")
            if counts.get(key, 1) > 1:
                lines.append(f"  - Repetition signal: seen {counts[key]} times; becoming repetitive.")
        lines.extend(["", "## Curator candidates", str(curator_candidates)])
        store.append_change_record({"timestamp": datetime.now(timezone.utc).isoformat(), "task_id": task_id, "suggestion_keys": keys})
        return "\n".join(lines).rstrip() + "\n"
