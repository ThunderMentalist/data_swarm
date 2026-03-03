"""Triage change request agent and repetition detection."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class TriageChangeAgent:
    """Triage Change Agent."""

    name = "Triage Change Agent"

    def generate(
        self,
        task_id: str,
        critic_eval: dict,
        curator_candidates: dict,
        home: Path,
    ) -> str:
        """Generate per-task change request and update global history/index."""
        history_dir = home / "triage_policy" / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        history_file = history_dir / "triage_change_requests.jsonl"
        repetition_file = history_dir / "repetition_index.json"

        repetition_index: dict[str, int] = {}
        if repetition_file.exists():
            repetition_index = json.loads(repetition_file.read_text(encoding="utf-8") or "{}")

        suggestions = critic_eval.get("suggestions", [])
        suggestion_keys: list[str] = []
        lines = ["# Triage Change Request", "", "## Suggested changes"]
        for suggestion in suggestions:
            title = suggestion.get("title", "Untitled suggestion")
            rationale = suggestion.get("rationale", "")
            evidence = suggestion.get("evidence", "")
            key = title.strip().lower().replace(" ", "_")
            suggestion_keys.append(key)
            count = repetition_index.get(key, 0) + 1
            repetition_index[key] = count
            lines.extend(
                [
                    f"- **{title}**",
                    f"  - Rationale: {rationale}",
                    f"  - Evidence: {evidence}",
                ]
            )
            if count > 1:
                lines.append(f"  - Repetition signal: seen {count} times; becoming repetitive.")

        lines.extend(["", "## Curator candidates", json.dumps(curator_candidates, indent=2)])

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "suggestion_keys": suggestion_keys,
            "titles": [s.get("title", "") for s in suggestions],
        }
        with history_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        repetition_file.write_text(json.dumps(repetition_index, indent=2), encoding="utf-8")
        return "\n".join(lines).rstrip() + "\n"
