"""Execution context shared by runner and stage instances."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from data_swarm.llm import LLMProfile, resolve_llm_profile


@dataclass
class ExecutionContext:
    """Runtime context carrying resolved LLM profile routing."""

    config: dict[str, Any]
    _cache: dict[str, LLMProfile] = field(default_factory=dict)

    def llm_profile(self, key: str, fallback: str | None = None) -> LLMProfile:
        """Resolve and cache profile by key."""
        cache_key = f"{key}|{fallback or ''}"
        if cache_key not in self._cache:
            self._cache[cache_key] = resolve_llm_profile(self.config, key, fallback=fallback)
        return self._cache[cache_key]

    def try_llm_profile(self, key: str, fallback: str | None = None) -> LLMProfile | None:
        """Resolve profile when configured; otherwise return None."""
        try:
            return self.llm_profile(key, fallback=fallback)
        except KeyError:
            return None
