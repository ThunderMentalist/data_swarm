"""I/O abstractions for HITL interactions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class UserIO(Protocol):
    """Protocol for interactive input/output."""

    def ask(self, prompt: str) -> str:
        """Prompt user and return response."""

    def tell(self, message: str) -> None:
        """Display a message to user."""


class ConsoleIO:
    """Console-backed implementation of UserIO."""

    def ask(self, prompt: str) -> str:
        """Prompt through stdin/stdout."""
        return input(prompt)

    def tell(self, message: str) -> None:
        """Print message to stdout."""
        print(message)


@dataclass
class FakeIO:
    """Deterministic fake I/O for tests."""

    answers: list[str] = field(default_factory=list)
    prompts: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def ask(self, prompt: str) -> str:
        """Return queued answer for the prompt."""
        self.prompts.append(prompt)
        if not self.answers:
            return ""
        return self.answers.pop(0)

    def tell(self, message: str) -> None:
        """Store outbound message."""
        self.messages.append(message)
