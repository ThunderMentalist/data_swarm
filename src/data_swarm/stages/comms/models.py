"""Typed comms stage models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class ChannelDraft:
    channel: str
    target_audience: str
    intent: str
    cta: str
    draft: str
    approval_status: str = "draft"
    notes: str = ""


@dataclass
class CommsPackage:
    channels: list[ChannelDraft] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"channels": [asdict(channel) for channel in self.channels]}

    @classmethod
    def from_dict(cls, payload: dict) -> "CommsPackage":
        return cls(channels=[ChannelDraft(**row) for row in payload.get("channels", [])])
