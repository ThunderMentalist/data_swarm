"""Configuration loading utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from data_swarm import yaml_compat as yaml
from data_swarm.tools.dotenv import load_dotenv

DEFAULT_CONFIG = {
    "timezone": "Europe/London",
    "llm": {"provider": "openai", "model": "gpt-4o-mini"},
    "triage": {
        "confidence_threshold": 0.6,
        "default_sensitivity": "internal",
        "risk_flags": ["timeline", "dependency", "stakeholder_alignment"],
    },
    "hitl": {
        "clarification_required": True,
        "comms_review_required": True,
        "patch_approval_required": True,
        "approve_after_test_failure": True,
    },
    "comms": {
        "default_style": "friendly_diplomatic",
        "leadership_style": "formal_concise",
        "political_two_variant": True,
    },
    "privacy": {"persist_identifiers": False, "require_role_mapping": True},
    "meridian_aux": {"max_files": 25, "max_chars": 60000, "max_debug_iterations": 3},
    "logging": {"level": "INFO"},
    "safety": {"never_write_outside_repo": True},
}

TONE_TEMPLATE = """# Tone Profile

## Baseline voice
- Friendly, diplomatic, and clear.
- Transparent about trade-offs without sounding vague.
- Avoid blunt or combative phrasing.

## Audience calibration
- **Peers:** collaborative and practical.
- **Senior leadership:** more formal, concise, and decision-oriented.

## Do / Don't examples
- Do: "Here is the recommended path and associated risk."
- Do: "I can provide a shorter executive summary if helpful."
- Don't: "This is obvious" or "You should have".
- Don't: overstate certainty when there are open unknowns.

## Custom phrases
- Add preferred openings, closings, and reusable snippets below.
"""

ENV_TEMPLATE = """# Local environment variables for data_swarm
# Do not commit secrets.
# OPENAI_API_KEY=
"""


@dataclass
class Config:
    """Resolved runtime config."""

    data_swarm_home: Path
    config_path: Path
    payload: dict[str, Any]

    @property
    def paths(self) -> dict[str, str]:
        """Return resolved paths map."""
        return self.payload.get("paths", {})


def detect_repo_root() -> Path:
    """Resolve repository root based on package location."""
    return Path(__file__).resolve().parents[2]


def default_data_swarm_home() -> Path:
    """Return DATA_SWARM_HOME path."""
    return Path(os.environ.get("DATA_SWARM_HOME", str(Path.home() / ".data_swarm"))).expanduser()


def detect_sibling_repo(repo_root: Path, name: str) -> Path:
    """Return sibling repo path or raise with guidance."""
    sibling = repo_root.parent / name
    if not sibling.exists():
        msg = (
            f"Unable to find {name!r} sibling repo at {sibling}. "
            f"Set paths.{name}_repo in ~/.data_swarm/config.yaml."
        )
        raise FileNotFoundError(msg)
    return sibling


def _merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def init_home(home: Path | None = None) -> Config:
    """Create data_swarm home scaffold and default config."""
    root = home or default_data_swarm_home()
    for p in ["tasks", "logs", "memory", "indexes"]:
        (root / p).mkdir(parents=True, exist_ok=True)
    cfg = root / "config.yaml"
    tone = root / "tone_profile.md"
    env_file = root / ".env"
    if not cfg.exists():
        cfg.write_text(yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False), encoding="utf-8")
    if not tone.exists():
        tone.write_text(TONE_TEMPLATE, encoding="utf-8")
    if not env_file.exists():
        env_file.write_text(ENV_TEMPLATE, encoding="utf-8")
    return load_config(root)


def load_config(home: Path | None = None) -> Config:
    """Load config and resolve defaults/autodetected paths."""
    data_home = home or default_data_swarm_home()
    load_dotenv(data_home / ".env")
    cfg_path = data_home / "config.yaml"
    payload: dict[str, Any] = dict(DEFAULT_CONFIG)
    if cfg_path.exists():
        payload = _merge(payload, yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {})
    paths = dict(payload.get("paths", {}))
    repo_root = Path(paths.get("repo_root", str(detect_repo_root())))
    paths.setdefault("repo_root", str(repo_root))
    paths.setdefault("meridian_repo", str(detect_sibling_repo(repo_root, "meridian")))
    paths.setdefault("meridian_aux_repo", str(detect_sibling_repo(repo_root, "meridian_aux")))
    payload["paths"] = paths
    return Config(data_swarm_home=data_home, config_path=cfg_path, payload=payload)
