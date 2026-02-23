"""Unified diff patch application with path safety."""

from __future__ import annotations

import subprocess
from pathlib import Path


class PatchSafetyError(RuntimeError):
    """Raised when patch attempts unsafe writes."""


def _extract_targets(diff_text: str) -> list[str]:
    targets: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            targets.append(line.removeprefix("+++ b/"))
    return targets


def apply_patch_safe(diff_text: str, target_repo: Path) -> None:
    """Apply patch only if all target files are under target repo."""
    for rel in _extract_targets(diff_text):
        candidate = (target_repo / rel).resolve()
        if target_repo.resolve() not in candidate.parents and candidate != target_repo.resolve():
            raise PatchSafetyError(f"Patch target outside repo: {rel}")
    subprocess.run(
        ["git", "-C", str(target_repo), "apply", "--whitespace=nowarn", "-"],
        input=diff_text,
        text=True,
        check=True,
    )
