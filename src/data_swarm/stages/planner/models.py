"""Typed planner stage models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class PlannerPlan:
    objective: str
    milestones: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    approvals: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    mitigation: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "PlannerPlan":
        base = cls(objective="")
        data = {}
        for key, default in base.to_dict().items():
            data[key] = payload.get(key, default)
        return cls(**data)


@dataclass
class PlannerCriticEvaluation:
    strengths: list[str]
    gaps: list[str]
    compliance_score: int
    suggestions: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
