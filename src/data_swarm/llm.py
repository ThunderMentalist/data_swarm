"""LLM profile and provider helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping


class LLMUnavailableError(RuntimeError):
    """Raised when LLM cannot be used."""


@dataclass(frozen=True)
class LLMProfile:
    """Resolved LLM profile used for a single model invocation."""

    model: str
    reasoning_effort: str | None = None
    verbosity: str | None = None
    max_output_tokens: int | None = None


def _profile_from_mapping(payload: Mapping[str, Any]) -> LLMProfile:
    return LLMProfile(
        model=str(payload.get("model", "")),
        reasoning_effort=payload.get("reasoning_effort"),
        verbosity=payload.get("verbosity"),
        max_output_tokens=payload.get("max_output_tokens"),
    )


def resolve_llm_profile(config: Mapping[str, Any], key: str, fallback: str | None = None) -> LLMProfile:
    """Resolve an LLM profile by key with inheritance from llm.defaults."""
    llm_cfg = config.get("llm", {})
    defaults = dict(llm_cfg.get("defaults", {}))
    legacy_model = llm_cfg.get("model")
    if legacy_model and "model" not in defaults:
        defaults["model"] = legacy_model
    profiles = llm_cfg.get("profiles", {})

    profile_cfg = dict(defaults)
    selected = profiles.get(key)
    if selected is None and fallback:
        selected = profiles.get(fallback)
    if selected:
        profile_cfg.update(selected)

    profile = _profile_from_mapping(profile_cfg)
    if not profile.model:
        raise KeyError(f"No model configured for profile '{key}'")
    return profile


class OpenAIProvider:
    """Minimal OpenAI provider wrapper."""

    def __init__(self, profile: str | LLMProfile) -> None:
        self.profile = profile if isinstance(profile, LLMProfile) else LLMProfile(model=profile)

    def _client(self, key: str) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMUnavailableError("Install extras: pip install -e .[openai]") from exc
        return OpenAI(api_key=key)

    def _request_payload(self, prompt: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.profile.model,
            "input": prompt,
        }
        if self.profile.reasoning_effort:
            payload["reasoning"] = {"effort": self.profile.reasoning_effort}
        if self.profile.verbosity:
            payload["text"] = {"verbosity": self.profile.verbosity}
        if self.profile.max_output_tokens is not None:
            payload["max_output_tokens"] = self.profile.max_output_tokens
        return payload

    def complete(self, prompt: str) -> str:
        """Run chat completion with graceful API key handling."""
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise LLMUnavailableError("OPENAI_API_KEY is not set. Configure DATA_SWARM_HOME/.env or env vars.")
        client = self._client(key)
        resp = client.responses.create(**self._request_payload(prompt))
        return resp.output_text
