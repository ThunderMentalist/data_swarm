"""Reusable policy pack storage and repetition tracking for stages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PolicyPack:
    """Policy content loaded for a stage."""

    core_prompt: str
    behaviour_cards: list[str]
    decision_trees: list[str]


class StagePolicyStore:
    """Read/write helpers for stage policy assets and learning history."""

    def __init__(self, home: Path, stage_key: str):
        self.root = home / f"{stage_key}_policy"
        self.active_cards = self.root / "active" / "behaviour_cards"
        self.active_trees = self.root / "active" / "decision_trees"
        self.archive_cards = self.root / "archive" / "behaviour_cards"
        self.archive_trees = self.root / "archive" / "decision_trees"
        self.history_dir = self.root / "history"
        self.history_jsonl = self.history_dir / f"{stage_key}_change_requests.jsonl"
        self.repetition_index = self.history_dir / "repetition_index.json"

    def ensure_scaffold(self) -> None:
        """Create stage policy scaffold and history files when absent."""
        for folder in [
            self.active_cards,
            self.active_trees,
            self.archive_cards,
            self.archive_trees,
            self.history_dir,
        ]:
            folder.mkdir(parents=True, exist_ok=True)
        core_path = self.root / "core_prompt.md"
        if not core_path.exists():
            core_path.write_text("", encoding="utf-8")
        self.history_jsonl.touch(exist_ok=True)
        if not self.repetition_index.exists():
            self.repetition_index.write_text("{}", encoding="utf-8")

    def load_policy_pack(self) -> PolicyPack:
        """Load active policy documents only."""
        self.ensure_scaffold()
        core_prompt = (self.root / "core_prompt.md").read_text(encoding="utf-8")
        return PolicyPack(
            core_prompt=core_prompt,
            behaviour_cards=self._load_files(self.active_cards),
            decision_trees=self._load_files(self.active_trees),
        )

    def append_change_record(self, record: dict) -> None:
        """Append a JSON record to stage history."""
        self.ensure_scaffold()
        with self.history_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def update_repetition_index(self, keys: list[str]) -> dict[str, int]:
        """Increment repetition counters and return updated map."""
        self.ensure_scaffold()
        current = json.loads(self.repetition_index.read_text(encoding="utf-8") or "{}")
        for key in keys:
            current[key] = int(current.get(key, 0)) + 1
        self.repetition_index.write_text(json.dumps(current, indent=2), encoding="utf-8")
        return {str(k): int(v) for k, v in current.items()}

    @staticmethod
    def _load_files(folder: Path) -> list[str]:
        if not folder.exists():
            return []
        return [path.read_text(encoding="utf-8") for path in sorted(p for p in folder.iterdir() if p.is_file())]
