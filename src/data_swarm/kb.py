"""Knowledge base loading and stage-context selection helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from data_swarm import yaml_compat as yaml
from data_swarm.stages.policy_store import PolicyPack, StagePolicyStore


_STAGE_KB_KEYS: dict[str, list[str]] = {
    "triage": ["role_registry", "org_units", "personas", "stakeholder_profiles"],
    "planner": ["role_registry", "org_units", "politics_map"],
    "stakeholder": ["stakeholder_profiles", "personas", "politics_map", "role_registry"],
    "navigation": ["politics_map", "org_units", "role_registry"],
    "comms": ["comms_patterns", "personas", "tone_profile"],
    "reaction": ["personas", "stakeholder_profiles", "role_registry", "politics_map"],
    "readiness": ["personas", "stakeholder_profiles", "role_registry"],
}


def load_kb(home: Path) -> dict[str, Any]:
    """Load all YAML files under DATA_SWARM_HOME/kb."""
    kb_dir = home / "kb"
    payload: dict[str, Any] = {}
    if not kb_dir.exists():
        return payload
    for path in sorted(kb_dir.glob("*.yaml")):
        payload[path.stem] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload


def load_stage_policy(home: Path, stage_key: str) -> PolicyPack:
    """Load the typed policy pack for a stage."""
    return StagePolicyStore(home, stage_key).load_policy_pack()


def select_stage_kb_context(stage_key: str, kb: dict[str, Any]) -> dict[str, Any]:
    """Return stage-relevant KB subset for deterministic stage behavior."""
    keys = _STAGE_KB_KEYS.get(stage_key, sorted(kb.keys()))
    return {key: kb.get(key, {}) for key in keys}
