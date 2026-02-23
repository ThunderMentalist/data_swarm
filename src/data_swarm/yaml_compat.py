"""Small YAML compatibility layer with JSON fallback."""

from __future__ import annotations

import json
from typing import Any

try:
    import yaml as _yaml
except ModuleNotFoundError:  # pragma: no cover
    _yaml = None


def safe_load(text: str) -> Any:
    """Load YAML-like text."""
    if _yaml:
        return _yaml.safe_load(text)
    if not text.strip():
        return None
    return json.loads(text)


def safe_dump(data: Any, sort_keys: bool = False) -> str:
    """Dump YAML-like text."""
    if _yaml:
        return _yaml.safe_dump(data, sort_keys=sort_keys)
    return json.dumps(data, indent=2)
