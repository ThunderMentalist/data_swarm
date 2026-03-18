"""CLI entrypoint for data-swarm."""

from __future__ import annotations

import argparse
import uuid
from pathlib import Path

from data_swarm.config import init_home, load_config
from data_swarm.orchestrator.reopen import reopen_task
from data_swarm.orchestrator.run_mode import RunMode, resolve_run_mode
from data_swarm.orchestrator.runner import run_task
from data_swarm.orchestrator.task_models import Task
from data_swarm.projects.meridian_aux.tools.indexer import build_index
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.task_store import TaskStore


def _cmd_init() -> None:
    cfg = init_home()
    print(f"Initialized DATA_SWARM_HOME at {cfg.data_swarm_home}")
    print("Next steps: set OPENAI_API_KEY in ~/.data_swarm/.env or shell env.")


def _cmd_task_new(args: argparse.Namespace) -> None:
    cfg = load_config()
    mode = resolve_run_mode(args.run_mode)
    task = Task(task_id=str(uuid.uuid4())[:8], title=args.title, description=args.description, task_type=args.task_type, run_mode=args.run_mode or "", is_demo=(mode is RunMode.DEMO))
    store = TaskStore(cfg.data_swarm_home)
    store.create(task)
    print(task.task_id)


def _cmd_task_run(args: argparse.Namespace) -> None:
    cfg = load_config()
    run_task(args.task_id, cfg.payload, cfg.data_swarm_home, run_mode_override=args.run_mode or "")


def _cmd_task_status(args: argparse.Namespace) -> None:
    cfg = load_config()
    task = TaskStore(cfg.data_swarm_home).load(args.task_id)
    print(f"{task.task_id}: {task.state.value}")


def _cmd_task_attach(args: argparse.Namespace) -> None:
    cfg = load_config()
    store = TaskStore(cfg.data_swarm_home)
    row = store.register_attachment(args.task_id, Path(args.file), notes=args.notes or "")
    print(f"registered {row['filename']} ({row['sha256'][:8]})")


def _cmd_task_reopen(args: argparse.Namespace) -> None:
    cfg = load_config()
    store = TaskStore(cfg.data_swarm_home)
    logs = LogStore(store.task_dir(args.task_id))
    reopen_task(args.task_id, store, logs)
    print(args.task_id)


def _cmd_index_build(_: argparse.Namespace) -> None:
    cfg = load_config()
    idx = cfg.data_swarm_home / "indexes" / "meridian" / "index.sqlite"
    paths = cfg.payload["paths"]
    build_index(idx, [Path(paths["meridian_repo"]), Path(paths["meridian_aux_repo"])])
    print(f"Index built at {idx}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="data-swarm")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    task = sub.add_parser("task")
    task_sub = task.add_subparsers(dest="task_cmd", required=True)
    new = task_sub.add_parser("new")
    new.add_argument("--title", required=True)
    new.add_argument("--description", required=True)
    new.add_argument("--task-type", default="general")
    new.add_argument("--run-mode", choices=[m.value for m in RunMode], default="")
    run = task_sub.add_parser("run")
    run.add_argument("task_id")
    run.add_argument("--run-mode", choices=[m.value for m in RunMode], default="")
    status = task_sub.add_parser("status")
    status.add_argument("task_id")
    reopen = task_sub.add_parser("reopen")
    reopen.add_argument("task_id")
    attach = task_sub.add_parser("attach")
    attach.add_argument("task_id")
    attach.add_argument("file")
    attach.add_argument("--notes", default="")

    index = sub.add_parser("index")
    index_sub = index.add_subparsers(dest="index_cmd", required=True)
    index_sub.add_parser("build")

    args = parser.parse_args()
    if args.cmd == "init":
        _cmd_init()
    elif args.cmd == "task" and args.task_cmd == "new":
        _cmd_task_new(args)
    elif args.cmd == "task" and args.task_cmd == "run":
        _cmd_task_run(args)
    elif args.cmd == "task" and args.task_cmd == "status":
        _cmd_task_status(args)
    elif args.cmd == "task" and args.task_cmd == "attach":
        _cmd_task_attach(args)
    elif args.cmd == "task" and args.task_cmd == "reopen":
        _cmd_task_reopen(args)
    elif args.cmd == "index" and args.index_cmd == "build":
        _cmd_index_build(args)


if __name__ == "__main__":
    main()
