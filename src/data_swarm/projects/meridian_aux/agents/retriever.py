"""Retriever agent for evidence packet."""

from __future__ import annotations

from pathlib import Path

from data_swarm.projects.meridian_aux.tools.retriever import RepoFile, collect_snippets


class RetrieverAgent:
    """Collect evidence snippets from chosen files."""

    def retrieve(
        self,
        repos: dict[str, Path],
        files: list[RepoFile],
        out_dir: Path,
        max_chars: int,
    ) -> tuple[list[Path], int]:
        """Retrieve snippets."""
        return collect_snippets(repos, files, out_dir, max_chars)
