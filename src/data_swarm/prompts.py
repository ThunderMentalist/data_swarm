"""Prompt loading helpers."""

from __future__ import annotations

import json
from pathlib import Path


def load_prompt(repo_root: Path, rel_path: str) -> str:
    path = repo_root / rel_path
    return path.read_text(encoding="utf-8")


def build_agent_prompt(repo_root: Path, stage: str, agent: str, context: dict, include_knowledge: bool = True) -> str:
    parts = [load_prompt(repo_root, "prompts/system/global_system.md")]
    if include_knowledge:
        for p in sorted((repo_root / "prompts" / "knowledge").glob("*.md")):
            parts.append(p.read_text(encoding="utf-8"))
    parts.append(load_prompt(repo_root, f"prompts/stages/{stage}/{agent}.md"))
    parts.append("CONTEXT JSON\n" + json.dumps(context, sort_keys=True))
    return "\n\n".join(parts)
