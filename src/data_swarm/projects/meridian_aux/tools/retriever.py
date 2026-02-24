"""Evidence retrieval helpers."""

from __future__ import annotations

from pathlib import Path

RepoFile = tuple[str, str]


def collect_snippets(
    repos: dict[str, Path],
    files: list[RepoFile],
    out_dir: Path,
    max_chars: int,
) -> tuple[list[Path], int]:
    """Copy selected file snippets into evidence folder."""
    out_dir.mkdir(parents=True, exist_ok=True)
    used: list[Path] = []
    chars = 0
    for idx, (repo, rel) in enumerate(files):
        src = repos[repo] / rel
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8")
        if chars + len(text) > max_chars:
            break
        chars += len(text)
        sanitized = rel.replace("/", "_")
        dest = out_dir / f"{idx:02d}_{repo}__{sanitized}"
        dest.write_text(text, encoding="utf-8")
        used.append(dest)
    return used, chars
