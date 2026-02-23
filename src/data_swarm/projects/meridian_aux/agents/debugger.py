"""Debugger agent scaffold."""

from __future__ import annotations


class DebuggerAgent:
    """Placeholder debugger patch proposer."""

    def propose(self, traceback_text: str) -> str:
        """Return notes about debugging in absence of robust implementation."""
        return f"Debugger received traceback of length={len(traceback_text)}"
