"""Typed reaction and readiness models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class ReactionAnalysis:
    summary: str
    new_facts: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    commitments: list[str] = field(default_factory=list)
    clarified_constraints: list[str] = field(default_factory=list)
    impact_assessment: str = ""
    open_questions: list[str] = field(default_factory=list)
    readiness_recommendation: str = "AWAITING_REPLIES"
    readiness_reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "ReactionAnalysis":
        return cls(**{k: payload.get(k, getattr(cls(summary=""), k)) for k in cls(summary="").to_dict().keys()})


@dataclass
class ReadinessDecision:
    recommended_state: str
    rationale: str
    requires_operator_approval: bool = True

    def to_dict(self) -> dict:
        return asdict(self)
