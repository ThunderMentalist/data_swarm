"""Meridian_Aux deliverable workflow."""

from __future__ import annotations

import json
from pathlib import Path

from data_swarm.orchestrator.hitl import approve
from data_swarm.orchestrator.task_models import Task
from data_swarm.projects.meridian_aux.agents.codegen import CodegenAgent
from data_swarm.projects.meridian_aux.agents.debugger import DebuggerAgent
from data_swarm.projects.meridian_aux.agents.navigator import NavigatorAgent
from data_swarm.projects.meridian_aux.agents.retriever import RetrieverAgent
from data_swarm.projects.meridian_aux.tools.dependency_closure import dependency_closure
from data_swarm.projects.meridian_aux.tools.indexer import build_index
from data_swarm.projects.meridian_aux.tools.test_runner import run_pytest, run_snippet
from data_swarm.tools.diff import apply_patch_safe, summarize_patch
from data_swarm.tools.io import UserIO


class MeridianAuxProject:
    """Run Meridian_Aux codegen/debug workflow."""

    def __init__(self, config: dict, io: UserIO) -> None:
        self.config = config
        self.io = io

    def _patch_summary(self, patch: str) -> str:
        summary = summarize_patch(patch)
        return f"files={summary['files']} +{summary['added']} -{summary['removed']}"

    def run(self, task: Task, task_dir: Path) -> None:
        """Execute end-to-end plugin flow up to patch/test artifacts."""
        paths = self.config["paths"]
        meridian = Path(paths["meridian_repo"])
        meridian_aux = Path(paths["meridian_aux_repo"])
        repos = {meridian.name: meridian, meridian_aux.name: meridian_aux}
        index_path = Path(self.config["data_swarm_home"]) / "indexes" / "meridian" / "index.sqlite"
        build_index(index_path, [meridian, meridian_aux])

        cfg = self.config["meridian_aux"]
        evidence = task_dir / "07_deliverable" / "evidence"
        evidence.mkdir(parents=True, exist_ok=True)
        nav = NavigatorAgent().decide(index_path, task.description)
        (evidence / "00_navigation.json").write_text(json.dumps(nav, indent=2), encoding="utf-8")

        entrypoints = [(h["repo"], h["file_path"]) for h in nav.get("entrypoints", [])]
        selected, edges = dependency_closure(index_path, entrypoints, cfg["max_files"])
        snippets, used_chars = RetrieverAgent().retrieve(repos, selected, evidence / "snippets", cfg["max_chars"])
        (evidence / "context.md").write_text(
            "\n".join(
                [
                    "# Context Summary",
                    "## Selected entrypoints",
                    *[f"- {r}/{p}" for r, p in entrypoints],
                    "## Files included",
                    *[f"- {r}/{p}" for r, p in selected],
                    "## Import edges followed",
                    *[f"- {e['from']} -> {e['to']} ({e['import']})" for e in edges],
                    "## Budgets used",
                    f"- files: {len(selected)} / {cfg['max_files']}",
                    f"- chars: {used_chars} / {cfg['max_chars']}",
                ]
            ),
            encoding="utf-8",
        )

        context = (evidence / "context.md").read_text(encoding="utf-8")
        generated = CodegenAgent(self.config["llm"]["model"]).generate(
            Path(__file__).parent / "prompts" / "codegen.md",
            context,
        )
        deliverable = task_dir / "07_deliverable"
        patch = generated.get("patch", "")
        (deliverable / "patch.diff").write_text(patch, encoding="utf-8")
        (deliverable / "snippet.py").write_text(generated.get("snippet", ""), encoding="utf-8")
        (deliverable / "test_plan.md").write_text("\n".join(generated.get("tests_added", [])), encoding="utf-8")
        (deliverable / "notes.md").write_text(generated.get("notes", ""), encoding="utf-8")

        iteration = 0
        snippet_path = deliverable / "snippet.py"
        if patch:
            self.io.tell(f"Patch summary: {self._patch_summary(patch)}")
            if approve(self.io, "Approve patch apply to meridian_aux repo?"):
                apply_patch_safe(patch, meridian_aux)

        while True:
            s_code, s_out, s_err = run_snippet(snippet_path, meridian_aux)
            p_code, p_out, p_err = run_pytest(meridian_aux)
            (deliverable / "stdout.txt").write_text(s_out + "\n" + p_out, encoding="utf-8")
            (deliverable / "stderr.txt").write_text(s_err + "\n" + p_err, encoding="utf-8")
            (deliverable / "test_run.json").write_text(
                json.dumps({"snippet_exit": s_code, "pytest_exit": p_code, "iteration": iteration}, indent=2),
                encoding="utf-8",
            )
            if p_code == 0 and s_code == 0:
                break
            (deliverable / "traceback.txt").write_text(s_err + "\n" + p_err, encoding="utf-8")
            if iteration >= int(cfg.get("max_debug_iterations", 3)):
                break
            if not approve(self.io, "Tests failed. Approve debug iteration?"):
                break

            debug_context = (deliverable / "traceback.txt").read_text(encoding="utf-8")
            debug = DebuggerAgent(self.config["llm"]["model"]).propose(
                Path(__file__).parent / "prompts" / "debugger.md",
                debug_context,
            )
            (deliverable / f"debug_notes_{iteration + 1}.md").write_text(debug.get("notes", ""), encoding="utf-8")
            if debug.get("probe_snippet"):
                snippet_path.write_text(debug["probe_snippet"], encoding="utf-8")
            debug_patch = debug.get("patch", "")
            if not debug_patch:
                break
            self.io.tell(f"Debug patch summary: {self._patch_summary(debug_patch)}")
            if not approve(self.io, "Approve debug patch apply?"):
                break
            apply_patch_safe(debug_patch, meridian_aux)
            (deliverable / f"debug_patch_{iteration + 1}.diff").write_text(debug_patch, encoding="utf-8")
            iteration += 1

        (deliverable / "summary.md").write_text(
            f"# Meridian_Aux Summary\n\nIterations: {iteration}\nTests: snippet+pytest executed.\n",
            encoding="utf-8",
        )
