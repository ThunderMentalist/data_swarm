"""Run snippets and pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_snippet(snippet: Path, cwd: Path) -> tuple[int, str, str]:
    """Execute python snippet."""
    proc = subprocess.run([sys.executable, str(snippet)], cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def run_pytest(cwd: Path) -> tuple[int, str, str]:
    """Run pytest in target repository."""
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr
