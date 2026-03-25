from pathlib import Path

from data_swarm.tools.attachments import build_inventory, ingest_selected_attachments


def test_inventory_only_intake_behavior(tmp_path: Path) -> None:
    manifest = [{"filename": "a.txt", "path": "inputs/a.txt", "sha256": "x", "size_bytes": 1, "type": "txt"}]
    inventory = build_inventory(tmp_path, manifest)
    assert inventory["files"][0]["filename"] == "a.txt"


def test_selected_file_only_extraction(tmp_path: Path) -> None:
    task_dir = tmp_path
    inputs = task_dir / "inputs"
    inputs.mkdir()
    (inputs / "a.txt").write_text("alpha", encoding="utf-8")
    (inputs / "b.txt").write_text("beta", encoding="utf-8")
    manifest = [
        {"filename": "a.txt", "path": "inputs/a.txt", "sha256": "1", "size_bytes": 5, "type": "txt"},
        {"filename": "b.txt", "path": "inputs/b.txt", "sha256": "2", "size_bytes": 4, "type": "txt"},
    ]
    _, _, extracted = ingest_selected_attachments(task_dir, manifest, ["b.txt"], {}, enabled=True)
    assert "b.txt" in extracted
    assert "a.txt" not in extracted


def test_run_mode_disables_extraction(tmp_path: Path) -> None:
    task_dir = tmp_path
    inputs = task_dir / "inputs"
    inputs.mkdir()
    (inputs / "a.txt").write_text("alpha", encoding="utf-8")
    manifest = [{"filename": "a.txt", "path": "inputs/a.txt", "sha256": "1", "size_bytes": 5, "type": "txt"}]
    _, summary, extracted = ingest_selected_attachments(task_dir, manifest, ["a.txt"], {}, enabled=False)
    assert extracted == {}
    assert "disabled" in summary
