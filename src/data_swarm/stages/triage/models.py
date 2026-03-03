"""Canonical task brief model for triage stage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class TaskBrief:
    """Structured, version-stable task brief."""

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

    @classmethod
    def empty(cls) -> TaskBrief:
        """Return an empty task brief."""
        return cls(goal="", deliverable="", audience="", context="")

    def to_dict(self) -> dict:
        """Serialize task brief to dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> TaskBrief:
        """Deserialize task brief from dict."""
        return cls(
            goal=d.get("goal", ""),
            deliverable=d.get("deliverable", ""),
            audience=d.get("audience", ""),
            context=d.get("context", ""),
            constraints=list(d.get("constraints", [])),
            inputs_available=list(d.get("inputs_available", [])),
            deadline=d.get("deadline", ""),
            success_criteria=list(d.get("success_criteria", [])),
            unknowns=list(d.get("unknowns", [])),
            assumptions=list(d.get("assumptions", [])),
            risks=list(d.get("risks", [])),
        )
