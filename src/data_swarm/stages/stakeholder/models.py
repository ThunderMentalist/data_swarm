"""Typed stakeholder stage models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class StakeholderRole:
    role: str
    influence: str
    interest: str
    decision_rights: str
    stance: str
    engagement_plan: str
    escalation_path: str


@dataclass
class StakeholderMap:
    roles: list[StakeholderRole] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"roles": [asdict(role) for role in self.roles]}

    @classmethod
    def from_dict(cls, payload: dict) -> "StakeholderMap":
        return cls(roles=[StakeholderRole(**row) for row in payload.get("roles", [])])
