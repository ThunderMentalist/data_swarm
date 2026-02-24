"""Redaction and role-mapping utilities for feedback."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_swarm.tools.io import UserIO

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def find_identifiers(text: str) -> list[str]:
    """Find likely identifiers (emails)."""
    return sorted(set(EMAIL_RE.findall(text)))


def replace_identifiers(text: str, mapping: dict[str, str]) -> str:
    """Replace exact identifier matches with role tokens."""
    updated = text
    for source, role in mapping.items():
        updated = updated.replace(source, f"[{role}]")
    return updated


def redact_identifiers(text: str) -> str:
    """Redact likely identifiers from text."""
    return EMAIL_RE.sub("[REDACTED_EMAIL]", text)


def sanitize_feedback(text: str, io: UserIO) -> tuple[str, set[str]]:
    """Map discovered identifiers to roles, then redact remaining emails."""
    mapping: dict[str, str] = {}
    roles_used: set[str] = set()
    for identifier in find_identifiers(text):
        role = io.ask(f"Map identifier '{identifier}' to role token (example: Client Lead): ").strip()
        if role:
            mapping[identifier] = role
            roles_used.add(role)
    sanitized = replace_identifiers(text, mapping)
    sanitized = redact_identifiers(sanitized)
    additional = io.ask(
        "Any additional names to role-map before storing? "
        "(optional, comma-separated name:role): "
    ).strip()
    if additional:
        for pair in additional.split(","):
            if ":" not in pair:
                continue
            name, role = [p.strip() for p in pair.split(":", 1)]
            if name and role:
                sanitized = sanitized.replace(name, f"[{role}]")
                roles_used.add(role)
    return sanitized, roles_used
