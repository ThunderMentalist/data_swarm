from pathlib import Path

from data_swarm.config import init_home

EXPECTED_KB_FILES = {
    "org_units.yaml",
    "role_registry.yaml",
    "stakeholder_profiles.yaml",
    "politics_map.yaml",
    "comms_patterns.yaml",
}


def test_init_home_creates_kb_scaffold(tmp_path: Path) -> None:
    repo_root = tmp_path / "data_swarm"
    repo_root.mkdir()
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian_aux").mkdir()

    home = tmp_path / ".data_swarm"
    home.mkdir()
    config_text = (
        f'{{"paths": {{"repo_root": "{repo_root.as_posix()}"}}}}'
    )
    (home / "config.yaml").write_text(config_text, encoding="utf-8")

    init_home(home=home)

    kb_dir = home / "kb"
    assert kb_dir.exists()
    assert kb_dir.is_dir()

    actual_files = {path.name for path in kb_dir.iterdir() if path.is_file()}
    assert EXPECTED_KB_FILES.issubset(actual_files)
