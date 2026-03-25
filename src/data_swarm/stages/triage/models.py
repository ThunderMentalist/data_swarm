"""Typed models for triage stage outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class TaskBrief:
    goal: str
    deliverable: str
    audience: str
    context: str
    constraints: list[str] = field(default_factory=list)
    inputs_available: list[str] = field(default_factory=list)
    deadline: str = ""
    success_criteria: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    task_type: str = "general"
    requested_attachments: list[str] = field(default_factory=list)
    readiness_hints: list[str] = field(default_factory=list)

    @classmethod
    def empty(cls) -> "TaskBrief":
        return cls(goal="", deliverable="", audience="", context="")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TaskBrief":
        return cls(**{k: d.get(k, getattr(cls.empty(), k)) for k in cls.empty().to_dict().keys()})


@dataclass
class TriageCriticEvaluation:
    strengths: list[str]
    gaps: list[str]
    compliance_score: int
    policy_checks: list[str] = field(default_factory=list)
    suggestions: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TriageCuratorOutput:
    delta_learning_md: str
    candidates: dict


@dataclass
class TriageChangeRequest:
    markdown: str
