"""Filesystem helpers."""

from __future__ import annotations

from pathlib import Path


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text with parent creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
