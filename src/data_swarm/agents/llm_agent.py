"""LLM JSON-call helper."""

from __future__ import annotations

import json

from data_swarm.llm import OpenAIProvider


class LLMAgent:
    def __init__(self, cfg: dict) -> None:
        self.provider = OpenAIProvider(cfg)

    def call_json(self, prompt: str) -> dict | None:
        text = self.provider.complete(prompt)
        try:
            return json.loads(text)
        except Exception:
            return None
