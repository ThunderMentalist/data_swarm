"""Code generation agent for meridian aux."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from data_swarm.llm import LLMUnavailableError, OpenAIProvider


class CodegenAgent:
    """Generate patch/tests/snippets using provider output."""

    def __init__(self, model: str) -> None:
        self.provider = OpenAIProvider(model)

    def generate(self, prompt_path: Path, context: str) -> dict:
        """Generate machine-parseable payload."""
        prompt = prompt_path.read_text(encoding="utf-8") + "\n\n" + context
        try:
            text = self.provider.complete(prompt)
        except LLMUnavailableError as exc:
            return {
                "patch": "",
                "tests_added": [],
                "snippet": "",
                "notes": str(exc),
            }
        try:
            return yaml.safe_load(text)
        except Exception:
            return json.loads(text)
