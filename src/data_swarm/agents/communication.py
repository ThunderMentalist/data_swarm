"""Communication draft agent."""

from __future__ import annotations

from pathlib import Path

from data_swarm.agents.base import AgentResult, BaseAgent


class CommunicationAgent(BaseAgent):
    """Generate communication drafts using tone profile."""

    name = "communication"

    def run(self, tone_profile_path: Path, summary: str) -> AgentResult:
        tone = tone_profile_path.read_text(encoding="utf-8") if tone_profile_path.exists() else "Diplomatic"
        content = f"Tone:\n{tone}\n\nEmail Draft:\nHello team,\n\n{summary}\n\nThanks."
        return AgentResult(content=content)
