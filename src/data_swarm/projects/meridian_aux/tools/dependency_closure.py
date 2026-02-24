"""Dependency closure over indexed import edges."""

from __future__ import annotations

import sqlite3
from collections import deque
from pathlib import Path

RepoFile = tuple[str, str]


def _resolve_import(conn: sqlite3.Connection, repo: str, importer: str, imported: str) -> list[RepoFile]:
    if not imported:
        return []
    if imported.startswith("."):
        importer_module = importer.replace("/", ".").removesuffix(".py")
        base_parts = importer_module.split(".")[:-1]
        level = len(imported) - len(imported.lstrip("."))
        suffix = imported.lstrip(".")
        base = base_parts[: max(0, len(base_parts) - level + 1)]
        module = ".".join([*base, suffix] if suffix else base)
    else:
        module = imported
    rows = conn.execute(
        "SELECT repo, file_path FROM modules WHERE repo = ? AND (module_name = ? OR module_name LIKE ?)",
        (repo, module, f"{module}.%"),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def dependency_closure(
    index_path: Path,
    initial_files: list[RepoFile],
    max_files: int,
) -> tuple[list[RepoFile], list[dict[str, str]]]:
    """Follow imports for a bounded file closure."""
    seen: set[RepoFile] = set()
    ordered: list[RepoFile] = []
    edges: list[dict[str, str]] = []
    q: deque[RepoFile] = deque(initial_files)
    with sqlite3.connect(index_path) as conn:
        while q and len(ordered) < max_files:
            item = q.popleft()
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
            imports = conn.execute(
                "SELECT imported_module FROM imports WHERE repo = ? AND file_path = ?",
                item,
            ).fetchall()
            for (imported,) in imports:
                for resolved in _resolve_import(conn, item[0], item[1], imported):
                    edges.append(
                        {
                            "from": f"{item[0]}/{item[1]}",
                            "to": f"{resolved[0]}/{resolved[1]}",
                            "import": imported,
                        }
                    )
                    if resolved not in seen and len(ordered) + len(q) < max_files:
                        q.append(resolved)
    return ordered, edges
