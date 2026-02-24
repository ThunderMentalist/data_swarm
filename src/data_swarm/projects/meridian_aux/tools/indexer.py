"""AST index builder and search for Meridian repos."""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path


def _iter_py_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if ".git" not in p.parts]


def _module_name_from_path(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_index(index_path: Path, repos: list[Path]) -> None:
    """Build sqlite AST index for provided repos."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(index_path) as conn:
        conn.executescript(
            """
            DROP TABLE IF EXISTS symbols;
            DROP TABLE IF EXISTS modules;
            DROP TABLE IF EXISTS imports;
            CREATE TABLE symbols (
                repo TEXT,
                file_path TEXT,
                symbol TEXT,
                kind TEXT,
                lineno INTEGER,
                docstring TEXT
            );
            CREATE TABLE modules (
                repo TEXT,
                module_name TEXT,
                file_path TEXT
            );
            CREATE TABLE imports (
                repo TEXT,
                file_path TEXT,
                imported_module TEXT
            );
            """
        )
        for repo in repos:
            for path in _iter_py_files(repo):
                rel = path.relative_to(repo)
                rel_text = str(rel)
                module = _module_name_from_path(rel)
                conn.execute("INSERT INTO modules VALUES (?, ?, ?)", (repo.name, module, rel_text))
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        conn.execute(
                            "INSERT INTO symbols VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                repo.name,
                                rel_text,
                                node.name,
                                type(node).__name__,
                                getattr(node, "lineno", 1),
                                ast.get_docstring(node) or "",
                            ),
                        )
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            conn.execute("INSERT INTO imports VALUES (?, ?, ?)", (repo.name, rel_text, alias.name))
                    if isinstance(node, ast.ImportFrom):
                        mod = node.module or ""
                        if node.level:
                            mod = "." * node.level + mod
                        conn.execute("INSERT INTO imports VALUES (?, ?, ?)", (repo.name, rel_text, mod))


def search_index(index_path: Path, query: str, limit: int = 10) -> list[dict[str, str]]:
    """Search indexed symbols by substring."""
    with sqlite3.connect(index_path) as conn:
        rows = conn.execute(
            "SELECT repo, file_path, symbol, kind, lineno FROM symbols "
            "WHERE symbol LIKE ? OR file_path LIKE ? OR docstring LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    return [
        {"repo": r[0], "file_path": r[1], "symbol": r[2], "kind": r[3], "lineno": str(r[4])}
        for r in rows
    ]
