"""LLM provider wrapper."""

from __future__ import annotations

import os
from typing import Any


class LLMUnavailableError(RuntimeError):
    """Raised when LLM cannot be used."""


class OpenAIProvider:
    """Minimal OpenAI provider wrapper."""

    def __init__(self, model: str) -> None:
        self.model = model

    def _client(self, key: str) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMUnavailableError("Install extras: pip install -e .[openai]") from exc
        return OpenAI(api_key=key)

    def complete(self, prompt: str) -> str:
        """Run chat completion with graceful API key handling."""
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise LLMUnavailableError("OPENAI_API_KEY is not set. Configure DATA_SWARM_HOME/.env or env vars.")
        client = self._client(key)
        resp = client.responses.create(model=self.model, input=prompt)
        return resp.output_text
