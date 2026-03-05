"""Conversation state helpers for stage-local model context."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversationMessage:
    """Single in-memory conversation message."""

    role: str
    content: str


@dataclass
class ConversationState:
    """Compact conversation buffer.

    Raw turns are intentionally in-memory only for a single run.
    Persisted data should always be compact summaries produced externally.
    """

    messages: list[ConversationMessage] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        """Append one message."""
        self.messages.append(ConversationMessage(role=role, content=content))

    def to_compact_context(self, limit: int = 8) -> list[dict[str, str]]:
        """Return a compact representation for model calls."""
        return [
            {"role": item.role, "content": item.content}
            for item in self.messages[-limit:]
        ]

