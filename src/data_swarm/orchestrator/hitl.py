"""Human-in-the-loop helpers."""

from __future__ import annotations

from data_swarm.tools.io import UserIO


def ask_yes_no(io: UserIO, prompt: str, default_no: bool = True) -> bool:
    """Request binary approval from user and return True only for explicit yes."""
    suffix = " [y/N]: " if default_no else " [Y/n]: "
    answer = io.ask(f"{prompt}{suffix}").strip().lower()
    if answer == "y":
        return True
    if not answer and not default_no:
        return True
    return False


def ask_multiline(io: UserIO, prompt: str, end_token: str = "END") -> str:
    """Capture multiline input until end token is entered on its own line."""
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
    """Request binary approval from user."""
    return ask_yes_no(io, prompt, default_no=True)


def comms_review(io: UserIO, drafts: dict[str, str]) -> dict[str, dict[str, str]]:
    """Collect approved comms copy per channel using multiline paste support."""
    reviewed: dict[str, dict[str, str]] = {}
    for channel, draft in drafts.items():
        io.tell(f"\n[{channel}] Draft:\n{draft}\n")
        edited = ask_multiline(
            io,
            f"Paste approved {channel} copy; END to finish; submit empty (END immediately) to accept draft",
        )
        reviewed[channel] = {"draft": draft, "approved": edited or draft}
    return reviewed
