from pathlib import Path

import pytest

from data_swarm.tools.diff import PatchSafetyError, apply_patch_safe


def test_patch_rejects_outside_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    diff = """diff --git a/a.txt b/../evil.txt\n--- a/a.txt\n+++ b/../evil.txt\n@@ -0,0 +1 @@\n+oops\n"""
    with pytest.raises(PatchSafetyError):
        apply_patch_safe(diff, repo)
