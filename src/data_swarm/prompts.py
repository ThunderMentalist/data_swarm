"""Prompt documentation helpers.

Runtime stage behavior in data_swarm is deterministic and does not depend on parsing
markdown prompt files. This module is a docs utility for composing a readable prompt
bundle during offline review and testing.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_prompt(repo_root: Path, rel_path: str) -> str:
    """Load a markdown prompt document by relative path."""
    return (repo_root / rel_path).read_text(encoding="utf-8")


def build_agent_prompt(repo_root: Path, stage: str, agent: str, context: dict, include_knowledge: bool = True) -> str:
    """Build a non-authoritative docs prompt bundle for debugging/spec review only."""
    parts = [load_prompt(repo_root, "prompts/system/global_system.md")]
    if include_knowledge:
        for p in sorted((repo_root / "prompts" / "knowledge").glob("*.md")):
            parts.append(p.read_text(encoding="utf-8"))
    parts.append(load_prompt(repo_root, f"prompts/stages/{stage}/{agent}.md"))
    parts.append("CONTEXT JSON\n" + json.dumps(context, sort_keys=True))
    parts.append("NOTE: Runtime does not parse markdown prompt docs for correctness.")
    return "\n\n".join(parts)
