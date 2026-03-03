from pathlib import Path

from data_swarm.config import init_home


def test_init_home_creates_policy_scaffolds(tmp_path: Path) -> None:
    repo_root = tmp_path / "data_swarm"
    repo_root.mkdir()
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian_aux").mkdir()

    home = tmp_path / ".data_swarm"
    home.mkdir()
    (home / "config.yaml").write_text(f'{{"paths": {{"repo_root": "{repo_root.as_posix()}"}}}}', encoding="utf-8")

    init_home(home=home)

    for key in ["triage", "planner", "stakeholder", "navigation", "comms"]:
        root = home / f"{key}_policy"
        assert (root / "active" / "behaviour_cards").exists()
        assert (root / "archive" / "decision_trees").exists()
        assert (root / "history" / f"{key}_change_requests.jsonl").exists()
        assert (root / "history" / "repetition_index.json").exists()
