"""Policy rendering helpers for triage stage."""

from __future__ import annotations

from data_swarm.stages.policy_store import PolicyPack

TriagePolicyPack = PolicyPack


def render_for_prompt(pack: PolicyPack) -> str:
    """Render policy sections for deterministic context composition."""
    cards = "\n\n".join(pack.behaviour_cards)
    trees = "\n\n".join(pack.decision_trees)
    return f"[CORE]\n{pack.core_prompt}\n\n[CARDS]\n{cards}\n\n[DECISION_TREES]\n{trees}".strip()
