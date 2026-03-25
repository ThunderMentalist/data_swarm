"""Reaction extraction helpers."""

from __future__ import annotations


def extract_reaction_signals(sentences: list[str]) -> dict[str, list[str]]:
    return {
        "facts": [s for s in sentences if any(k in s.lower() for k in ["is", "are", "observed"])][:5],
        "decisions": [s for s in sentences if any(k in s.lower() for k in ["decided", "approved", "chose"])][:5],
        "open_questions": [s for s in sentences if "?" in s or "question" in s.lower()][:5],
        "commitments": [s for s in sentences if any(k in s.lower() for k in ["will", "commit", "by "])][:5],
        "blockers": [s for s in sentences if any(k in s.lower() for k in ["blocked", "risk", "issue"])][:5],
    }
