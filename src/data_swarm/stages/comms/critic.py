"""Comms critic agent."""

from __future__ import annotations

from data_swarm.stages.policy_store import PolicyPack


class CommsCriticAgent:
    name = "Comms Critic Agent"

    def evaluate(self, initial_drafts: dict, final_comms: dict, policy: PolicyPack) -> dict:
        forbidden = [line.replace("forbidden:", "").strip().lower() for line in policy.core_prompt.splitlines() if line.startswith("forbidden:")]
        violations = []
        for row in final_comms.get("channels", []):
            text = row.get("draft", "").lower()
            for word in forbidden:
                if word and word in text:
                    violations.append(f"{row.get('channel')}: {word}")
        return {
            "strengths": ["Comms package includes required channels."],
            "gaps": violations or ["No major structural gaps detected."],
            "compliance_score": 100 - (15 * len(violations)),
            "suggestions": [{"title": "Add channel-specific call-to-action", "rationale": "Explicit asks improve response rates.", "evidence": f"channels={len(final_comms.get('channels', []))}", "suggestion_key": "comms_channel_cta"}],
        }
