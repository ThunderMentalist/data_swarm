"""Base classes for agentic stages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class StageResult:
    """Result returned by a stage execution."""

    approved: bool
    artifacts_written: list[str]


class ConciergeAgentBase(Protocol):
    """Protocol for concierge agents in agentic stages."""


class CriticAgentBase(Protocol):
    """Protocol for critic agents in agentic stages."""


class CuratorAgentBase(Protocol):
    """Protocol for curator agents in agentic stages."""


class ChangeAgentBase(Protocol):
    """Protocol for change agents in agentic stages."""


class AgenticStage:
    """Base class for stage orchestrators."""

    def run(self, *args: object, **kwargs: object) -> StageResult:
        """Run the stage."""
        raise NotImplementedError
