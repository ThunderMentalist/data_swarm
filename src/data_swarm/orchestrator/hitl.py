"""Human-in-the-loop helpers."""

from __future__ import annotations

from enum import Enum

from data_swarm.tools.io import UserIO


class StageGateAction(str, Enum):
    APPROVE_CONTINUE = "APPROVE_CONTINUE"
    REVISE_STAGE = "REVISE_STAGE"
    SKIP_STAGE = "SKIP_STAGE"
    PAUSE_BLOCKED = "PAUSE_BLOCKED"
    CLOSE_EARLY = "CLOSE_EARLY"


def ask_yes_no(io: UserIO, prompt: str, default_no: bool = True) -> bool:
    suffix = " [y/N]: " if default_no else " [Y/n]: "
    answer = io.ask(f"{prompt}{suffix}").strip().lower()
    if answer == "y":
        return True
    if not answer and not default_no:
        return True
    return False


def stage_gate(io: UserIO, stage_key: str) -> StageGateAction:
    """Prompt operator to approve/revise/skip/pause/close for a stage."""
    io.tell(f"Gate decision for {stage_key}:")
    io.tell("1) Approve & continue")
    io.tell("2) Revise this stage (iterate)")
    io.tell("3) Skip this stage")
    io.tell("4) Pause / Block task")
    io.tell("5) Close task early")
    choice = (io.ask("Select [1-5] (default 4): ").strip() or "4")
    return {
        "1": StageGateAction.APPROVE_CONTINUE,
        "2": StageGateAction.REVISE_STAGE,
        "3": StageGateAction.SKIP_STAGE,
        "4": StageGateAction.PAUSE_BLOCKED,
        "5": StageGateAction.CLOSE_EARLY,
    }.get(choice, StageGateAction.PAUSE_BLOCKED)


def ask_multiline(io: UserIO, prompt: str, end_token: str = "END") -> str:
    io.tell(prompt)
    io.tell(f"(Paste text. End with a line containing only {end_token})")
    lines: list[str] = []
    while True:
        line = io.ask("> ")
        if line.strip() == end_token:
            break
        lines.append(line)
    return "\n".join(lines).rstrip()


def approve(io: UserIO, prompt: str) -> bool:
    return ask_yes_no(io, prompt, default_no=True)


def comms_review(io: UserIO, drafts: dict[str, str]) -> dict[str, dict[str, str]]:
    reviewed: dict[str, dict[str, str]] = {}
    for channel, draft in drafts.items():
        io.tell(f"\n[{channel}] Draft:\n{draft}\n")
        edited = ask_multiline(
            io,
            f"Paste approved {channel} copy; END to finish; submit empty (END immediately) to accept draft",
        )
        reviewed[channel] = {"draft": draft, "approved": edited or draft}
    return reviewed
