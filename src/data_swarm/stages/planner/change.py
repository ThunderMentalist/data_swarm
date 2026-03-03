"""Planner change request agent."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from data_swarm.stages.policy_store import StagePolicyStore


class PlannerChangeAgent:
    """Planner Change Agent."""

    name = "Planner Change Agent"

    def generate(self, task_id: str, critic_eval: dict, curator_candidates: dict, home: Path) -> str:
        """Generate change request and persist repetition signals."""
        store = StagePolicyStore(home, "planner")
        store.ensure_scaffold()
        suggestions = critic_eval.get("suggestions", [])
        keys = [s.get("suggestion_key", "planner_suggestion") for s in suggestions]
        counts = store.update_repetition_index(keys)
        lines = ["# Planner Change Request", "", "## Suggested changes"]
        for suggestion, key in zip(suggestions, keys):
            lines.extend(
                [
                    f"- **{suggestion.get('title', 'Untitled suggestion')}**",
                    f"  - Rationale: {suggestion.get('rationale', '')}",
                    f"  - Evidence: {suggestion.get('evidence', '')}",
                ]
            )
            if counts.get(key, 1) > 1:
                lines.append(f"  - Repetition signal: seen {counts[key]} times; becoming repetitive.")
        lines.extend(["", "## Curator candidates", str(curator_candidates)])
        store.append_change_record(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task_id,
                "suggestion_keys": keys,
            }
        )
        return "\n".join(lines).rstrip() + "\n"
