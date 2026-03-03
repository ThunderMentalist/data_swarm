"""Comms critic agent."""

from __future__ import annotations


class CommsCriticAgent:
    """Comms Critic Agent."""

    name = "Comms Critic Agent"

    def evaluate(self, initial_drafts: dict[str, str], final_comms: dict[str, str]) -> dict:
        """Evaluate final comms package."""
        return {
            "strengths": ["Comms package includes all required channels."],
            "gaps": ["Template personalization can be improved."],
            "suggestions": [
                {
                    "title": "Add channel-specific call-to-action",
                    "rationale": "Explicit asks improve response rates.",
                    "evidence": f"Channels reviewed: {', '.join(sorted(final_comms))}",
                    "suggestion_key": "comms_channel_cta",
                }
            ],
        }
