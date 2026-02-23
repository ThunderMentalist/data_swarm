"""LLM provider wrapper."""

from __future__ import annotations

import os

from openai import OpenAI


class LLMUnavailableError(RuntimeError):
    """Raised when LLM cannot be used."""


class OpenAIProvider:
    """Minimal OpenAI provider wrapper."""

    def __init__(self, model: str) -> None:
        self.model = model

    def complete(self, prompt: str) -> str:
        """Run chat completion with graceful API key handling."""
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise LLMUnavailableError("OPENAI_API_KEY is not set. Configure ~/.data_swarm/.env or env vars.")
        client = OpenAI(api_key=key)
        resp = client.responses.create(model=self.model, input=prompt)
        return resp.output_text
