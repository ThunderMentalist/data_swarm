"""Typed navigation stage models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class NavigationPlan:
    outreach_sequence: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    gating_dependencies: list[str] = field(default_factory=list)
    political_risks: list[str] = field(default_factory=list)
    contingencies: list[str] = field(default_factory=list)
    escalation_triggers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "NavigationPlan":
        return cls(**{k: list(payload.get(k, [])) for k in cls().to_dict().keys()})
