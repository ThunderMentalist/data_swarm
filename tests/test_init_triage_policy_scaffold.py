from pathlib import Path

from data_swarm.config import init_home


def test_init_home_creates_triage_policy_scaffold(tmp_path: Path) -> None:
    repo_root = tmp_path / "data_swarm"
    repo_root.mkdir()
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian_aux").mkdir()

    home = tmp_path / ".data_swarm"
    home.mkdir()
    (home / "config.yaml").write_text(f'{{"paths": {{"repo_root": "{repo_root.as_posix()}"}}}}', encoding="utf-8")

    init_home(home=home)

    assert (home / "triage_policy" / "core_prompt.md").exists()
    assert (home / "triage_policy" / "active" / "behaviour_cards" / "example.md").exists()
    assert (home / "triage_policy" / "active" / "decision_trees" / "example.yaml").exists()
    assert (home / "triage_policy" / "history" / "repetition_index.json").exists()
