"""Policy pack loading for triage stage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TriagePolicyPack:
    """Runtime policy pack injected into triage concierge prompts."""

    core_prompt: str
    behaviour_cards: list[str]
    decision_trees: list[str]


def _load_contents(folder: Path) -> list[str]:
    if not folder.exists():
        return []
    return [path.read_text(encoding="utf-8") for path in sorted(p for p in folder.iterdir() if p.is_file())]


def load_policy_pack(home: Path) -> TriagePolicyPack:
    """Load active triage policy materials from DATA_SWARM_HOME."""
    policy_root = home / "triage_policy"
    core_path = policy_root / "core_prompt.md"
    core_prompt = core_path.read_text(encoding="utf-8") if core_path.exists() else ""
    behaviour_cards = _load_contents(policy_root / "active" / "behaviour_cards")
    decision_trees = _load_contents(policy_root / "active" / "decision_trees")
    return TriagePolicyPack(
        core_prompt=core_prompt,
        behaviour_cards=behaviour_cards,
        decision_trees=decision_trees,
    )


def render_for_prompt(pack: TriagePolicyPack) -> str:
    """Render policy sections for deterministic prompt composition."""
    cards = "\n\n".join(pack.behaviour_cards)
    trees = "\n\n".join(pack.decision_trees)
    return f"[CORE]\n{pack.core_prompt}\n\n[CARDS]\n{cards}\n\n[DECISION_TREES]\n{trees}".strip()
