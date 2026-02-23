"""Base agent abstractions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentResult:
    """Output from an agent run."""

    content: str
    confidence: float = 0.5


class BaseAgent:
    """Base deterministic/non-deterministic agent."""

    name = "base"

    def run(self, **_: object) -> AgentResult:
        """Run agent and return a result."""
        raise NotImplementedError
