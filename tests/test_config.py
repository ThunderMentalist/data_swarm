from pathlib import Path

import pytest

from data_swarm.config import load_config


def test_config_autodetect_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "data_swarm"
    repo.mkdir()
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian_aux").mkdir()
    home = tmp_path / ".data_swarm"
    home.mkdir()
    config_text = f'{{"paths": {{"repo_root": "{repo.as_posix()}"}}}}'
    (home / "config.yaml").write_text(config_text, encoding="utf-8")
    monkeypatch.setenv("DATA_SWARM_HOME", str(home))

    cfg = load_config(home)
    assert cfg.payload["paths"]["meridian_repo"].endswith("meridian")
    assert cfg.payload["paths"]["meridian_aux_repo"].endswith("meridian_aux")
