"""Meridian_Aux deliverable workflow."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm.orchestrator.task_models import Task
from data_swarm.projects.meridian_aux.agents.codegen import CodegenAgent
from data_swarm.projects.meridian_aux.agents.navigator import NavigatorAgent
from data_swarm.projects.meridian_aux.agents.retriever import RetrieverAgent
from data_swarm.projects.meridian_aux.tools.indexer import build_index
from data_swarm.projects.meridian_aux.tools.test_runner import run_pytest, run_snippet
from data_swarm.tools.diff import apply_patch_safe


class MeridianAuxProject:
    """Run Meridian_Aux codegen/debug workflow."""

    def __init__(self, config: dict) -> None:
        self.config = config

    def run(self, task: Task, task_dir: Path) -> None:
        """Execute end-to-end plugin flow up to patch/test artifacts."""
        paths = self.config["paths"]
        meridian = Path(paths["meridian_repo"])
        meridian_aux = Path(paths["meridian_aux_repo"])
        index_path = Path(self.config["data_swarm_home"]) / "indexes" / "meridian" / "index.sqlite"
        build_index(index_path, [meridian, meridian_aux])

        evidence = task_dir / "07_deliverable" / "evidence"
        evidence.mkdir(parents=True, exist_ok=True)
        nav = NavigatorAgent().decide(index_path, task.description)
        (evidence / "00_navigation.json").write_text(json.dumps(nav, indent=2), encoding="utf-8")

        paths_to_pull = [h["file_path"] for h in nav.get("entrypoints", []) if h["repo"] == meridian_aux.name]
        snippets = RetrieverAgent().retrieve(
            meridian_aux,
            paths_to_pull,
            evidence / "snippets",
            self.config["meridian_aux"]["max_chars"],
        )
        (evidence / "01_evidence_packet.md").write_text(
            "# Evidence\n" + "\n".join(str(s) for s in snippets),
            encoding="utf-8",
        )

        context = (evidence / "01_evidence_packet.md").read_text(encoding="utf-8")
        generated = CodegenAgent(self.config["llm"]["model"]).generate(
            Path(__file__).parent / "prompts" / "codegen.md", context
        )
        deliverable = task_dir / "07_deliverable"
        (deliverable / "patch.diff").write_text(generated.get("patch", ""), encoding="utf-8")
        (deliverable / "snippet.py").write_text(generated.get("snippet", ""), encoding="utf-8")
        (deliverable / "test_plan.md").write_text("\n".join(generated.get("tests_added", [])), encoding="utf-8")
        (deliverable / "notes.md").write_text(generated.get("notes", ""), encoding="utf-8")

        if generated.get("patch"):
            approve = input("Approve patch apply to meridian_aux repo? [y/N]: ").strip().lower()
            if approve == "y":
                apply_patch_safe(generated["patch"], meridian_aux)
                s_code, s_out, s_err = run_snippet(deliverable / "snippet.py", meridian_aux)
                p_code, p_out, p_err = run_pytest(meridian_aux)
                (deliverable / "stdout.txt").write_text(s_out + "\n" + p_out, encoding="utf-8")
                (deliverable / "stderr.txt").write_text(s_err + "\n" + p_err, encoding="utf-8")
                (deliverable / "test_run.json").write_text(
                    json.dumps({"snippet_exit": s_code, "pytest_exit": p_code}, indent=2),
                    encoding="utf-8",
                )
                if p_code != 0 or s_code != 0:
                    (deliverable / "traceback.txt").write_text(s_err + "\n" + p_err, encoding="utf-8")
                    input("Tests failed. Approve debug iteration? [enter to continue]")
