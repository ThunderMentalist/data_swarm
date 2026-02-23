"""Navigator agent for meridian aux."""

from __future__ import annotations

from data_swarm.projects.meridian_aux.tools.indexer import search_index


class NavigatorAgent:
    """Identify likely file entrypoints from index."""

    def decide(self, index_path, query: str) -> dict:
        """Return simple navigation decision."""
        hits = search_index(index_path, query, limit=5)
        return {"entrypoints": hits, "reason": "Top symbol/file matches for task query."}
