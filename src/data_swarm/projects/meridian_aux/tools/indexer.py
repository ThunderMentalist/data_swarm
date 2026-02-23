"""AST index builder and search for Meridian repos."""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path


def _iter_py_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if ".git" not in p.parts]


def build_index(index_path: Path, repos: list[Path]) -> None:
    """Build sqlite AST index for provided repos."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(index_path) as conn:
        conn.executescript(
            """
            DROP TABLE IF EXISTS symbols;
            CREATE TABLE symbols (
                repo TEXT,
                file_path TEXT,
                symbol TEXT,
                kind TEXT,
                lineno INTEGER,
                docstring TEXT
            );
            """
        )
        for repo in repos:
            for path in _iter_py_files(repo):
                rel = str(path.relative_to(repo))
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        conn.execute(
                            "INSERT INTO symbols VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                repo.name,
                                rel,
                                node.name,
                                type(node).__name__,
                                getattr(node, "lineno", 1),
                                ast.get_docstring(node) or "",
                            ),
                        )


def search_index(index_path: Path, query: str, limit: int = 10) -> list[dict[str, str]]:
    """Search indexed symbols by substring."""
    with sqlite3.connect(index_path) as conn:
        rows = conn.execute(
            "SELECT repo, file_path, symbol, kind, lineno FROM symbols WHERE symbol LIKE ? OR file_path LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    return [
        {"repo": r[0], "file_path": r[1], "symbol": r[2], "kind": r[3], "lineno": str(r[4])}
        for r in rows
    ]
