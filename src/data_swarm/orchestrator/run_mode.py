"""Run mode policy controls for lifecycle behavior."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RunMode(str, Enum):
    PROTOTYPE = "PROTOTYPE"
    CALIBRATION = "CALIBRATION"
    INITIAL_USING = "INITIAL_USING"
    STEADY_STATE = "STEADY_STATE"
    STEP_CHANGE = "STEP_CHANGE"
    DEMO = "DEMO"


@dataclass(frozen=True)
class RunModePolicy:
    allow_policy_history_write: bool
    allow_persona_learning: bool
    allow_kb_apply_prompt: bool
    allow_memory_write: bool
    strict_redaction: bool
    watermark_demo_artifacts: bool
    attachment_ingest_enabled: bool


def policy_for_mode(mode: RunMode) -> RunModePolicy:
    """Return effective policy switches for a mode."""
    if mode is RunMode.PROTOTYPE:
        return RunModePolicy(False, False, False, False, True, False, False)
    if mode is RunMode.CALIBRATION:
        return RunModePolicy(True, True, False, False, True, False, True)
    if mode is RunMode.DEMO:
        return RunModePolicy(False, False, False, False, True, True, False)
    return RunModePolicy(True, True, True, True, False, False, True)


def resolve_run_mode(value: str | None, fallback: str = "INITIAL_USING") -> RunMode:
    """Parse run mode strings safely."""
    raw = (value or fallback or "INITIAL_USING").strip().upper()
    try:
        return RunMode(raw)
    except ValueError:
        return RunMode.INITIAL_USING
