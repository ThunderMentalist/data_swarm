"""Redaction utilities for identifiers."""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def find_identifiers(text: str) -> list[str]:
    """Find likely identifiers (emails)."""
    return EMAIL_RE.findall(text)


def redact_identifiers(text: str) -> str:
    """Redact likely identifiers from text."""
    return EMAIL_RE.sub("[REDACTED_EMAIL]", text)
