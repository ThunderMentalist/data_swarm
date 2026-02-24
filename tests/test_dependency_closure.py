from pathlib import Path

from data_swarm.projects.meridian_aux.tools.dependency_closure import dependency_closure
from data_swarm.projects.meridian_aux.tools.indexer import build_index


def test_dependency_closure_follows_imports(tmp_path: Path) -> None:
    meridian = tmp_path / "meridian"
    meridian_aux = tmp_path / "meridian_aux"
    meridian.mkdir()
    meridian_aux.mkdir()

    (meridian / "shared.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    (meridian_aux / "util.py").write_text("def x():\n    return 1\n", encoding="utf-8")
    (meridian_aux / "main.py").write_text("import util\n", encoding="utf-8")

    idx = tmp_path / "index.sqlite"
    build_index(idx, [meridian, meridian_aux])

    files, _ = dependency_closure(idx, [("meridian_aux", "main.py")], max_files=5)
    assert ("meridian_aux", "main.py") in files
    assert ("meridian_aux", "util.py") in files
