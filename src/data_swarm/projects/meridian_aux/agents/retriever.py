"""Retriever agent for evidence packet."""

from __future__ import annotations

from pathlib import Path

from data_swarm.projects.meridian_aux.tools.retriever import collect_snippets


class RetrieverAgent:
    """Collect evidence snippets from chosen files."""

    def retrieve(self, repo: Path, file_paths: list[str], out_dir: Path, max_chars: int) -> list[Path]:
        """Retrieve snippets."""
        return collect_snippets(repo, file_paths, out_dir, max_chars)
