"""Policy pack loading for triage stage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from data_swarm.stages.policy_store import StagePolicyStore


@dataclass
class TriagePolicyPack:
    """Runtime policy pack injected into triage concierge prompts."""

    core_prompt: str
    behaviour_cards: list[str]
    decision_trees: list[str]


def load_policy_pack(home: Path) -> TriagePolicyPack:
    """Load active triage policy materials from DATA_SWARM_HOME."""
    pack = StagePolicyStore(home, "triage").load_policy_pack()
    return TriagePolicyPack(
        core_prompt=pack.core_prompt,
        behaviour_cards=pack.behaviour_cards,
        decision_trees=pack.decision_trees,
    )


def render_for_prompt(pack: TriagePolicyPack) -> str:
    """Render policy sections for deterministic prompt composition."""
    cards = "\n\n".join(pack.behaviour_cards)
    trees = "\n\n".join(pack.decision_trees)
    return f"[CORE]\n{pack.core_prompt}\n\n[CARDS]\n{cards}\n\n[DECISION_TREES]\n{trees}".strip()
