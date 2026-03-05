"""Knowledge base loading and proposal application helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from data_swarm import yaml_compat as yaml


def load_kb(home: Path) -> dict[str, Any]:
    """Load all YAML files under DATA_SWARM_HOME/kb."""
    kb_dir = home / "kb"
    payload: dict[str, Any] = {}
    if not kb_dir.exists():
        return payload
    for path in sorted(kb_dir.glob("*.yaml")):
        payload[path.stem] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload


def load_stage_policy(home: Path, stage_key: str) -> dict[str, Any]:
    """Load stage policy pack deterministically."""
    root = home / f"{stage_key}_policy"
    core = root / "core_prompt.md"
    cards = sorted((root / "active" / "behaviour_cards").glob("*")) if (root / "active" / "behaviour_cards").exists() else []
    trees = sorted((root / "active" / "decision_trees").glob("*")) if (root / "active" / "decision_trees").exists() else []
    return {
        "core_prompt": core.read_text(encoding="utf-8") if core.exists() else "",
        "behaviour_cards": [p.read_text(encoding="utf-8") for p in cards if p.is_file()],
        "decision_trees": [p.read_text(encoding="utf-8") for p in trees if p.is_file()],
    }
