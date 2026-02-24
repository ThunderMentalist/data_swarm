"""Debugger agent implementation."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from data_swarm.llm import LLMUnavailableError, OpenAIProvider


class DebuggerAgent:
    """Propose bounded debug patch outputs."""

    def __init__(self, model: str) -> None:
        self.provider = OpenAIProvider(model)

    def propose(self, prompt_path: Path, context: str) -> dict[str, str]:
        """Return patch, probe snippet, and notes."""
        prompt = prompt_path.read_text(encoding="utf-8") + "\n\n" + context
        try:
            text = self.provider.complete(prompt)
        except LLMUnavailableError as exc:
            return {"patch": "", "probe_snippet": "", "notes": str(exc)}
        try:
            payload = yaml.safe_load(text)
        except Exception:
            payload = json.loads(text)
        return {
            "patch": payload.get("patch", ""),
            "probe_snippet": payload.get("probe_snippet", ""),
            "notes": payload.get("notes", ""),
        }
