"""Helpers for loading upstream stage artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(task_dir: Path, rel_path: str) -> dict[str, Any]:
    path = task_dir / rel_path
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(task_dir: Path, rel_path: str) -> str:
    path = task_dir / rel_path
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_stage_inputs(task_dir: Path) -> dict[str, Any]:
    """Return core cross-stage artifacts used by later stages."""
    return {
        "triage": load_json(task_dir, "01_triage/final_brief.json"),
        "planner": load_json(task_dir, "02_plan/02_plan.json"),
        "stakeholder": load_json(task_dir, "03_stakeholders/03_stakeholders.json"),
        "navigation": load_json(task_dir, "04_navigation/04_navigation.json"),
        "comms": load_json(task_dir, "05_comms/final_comms.json"),
        "reaction": load_json(task_dir, "06_reaction/final_reaction.json"),
    }
