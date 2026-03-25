"""Attachment inventory + ingest helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_inventory(task_dir: Path, manifest_rows: list[dict]) -> dict[str, Any]:
    files = []
    for row in manifest_rows:
        files.append({
            "filename": row.get("filename", ""),
            "path": row.get("path", ""),
            "sha256": row.get("sha256", ""),
            "size_bytes": row.get("size_bytes", 0),
            "type": row.get("type", ""),
            "notes": row.get("notes", ""),
        })
    return {"task_dir": str(task_dir), "files": files}


def extract_text(task_dir: Path, row: dict, max_chars: int) -> tuple[str, str]:
    path = task_dir / row.get("path", "")
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "", "PDF not ingested; provide txt/docx export."
    if ext in {".txt", ".md", ".csv", ".tsv", ".json", ".yaml", ".yml"}:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            return text[:max_chars], ""
        except OSError as exc:
            return "", str(exc)
    return "", "unsupported file type"


def ingest_selected_attachments(task_dir: Path, manifest_rows: list[dict], requested_filenames: list[str], cfg: dict, enabled: bool = True) -> tuple[dict, str, dict[str, str]]:
    max_chars = int(cfg.get("max_chars_per_file", 20000))
    max_files = int(cfg.get("max_files", 25))
    inventory = build_inventory(task_dir, manifest_rows[:max_files])
    if not enabled:
        return inventory, "# Attachments Summary\n\n- extraction disabled by run mode\n", {}
    selected = {name.strip() for name in requested_filenames if name.strip()}
    extracted: dict[str, str] = {}
    lines = ["# Attachments Summary", ""]
    for row in manifest_rows[:max_files]:
        fn = row.get("filename", "unknown")
        if selected and fn not in selected:
            lines.append(f"- {fn}: skipped (not requested by triage)")
            continue
        text, note = extract_text(task_dir, row, max_chars)
        lines.append(f"- {fn}: {note or 'ingested'}")
        if text:
            extracted[fn] = text
    return inventory, "\n".join(lines) + "\n", extracted
