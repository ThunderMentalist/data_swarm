"""CLI entrypoint for data-swarm."""

from __future__ import annotations

import argparse
import uuid
from pathlib import Path

from data_swarm.config import init_home, load_config
from data_swarm.orchestrator.runner import run_task
from data_swarm.orchestrator.task_models import Task
from data_swarm.projects.meridian_aux.tools.indexer import build_index
from data_swarm.stores.task_store import TaskStore


def _cmd_init() -> None:
    cfg = init_home()
    print(f"Initialized DATA_SWARM_HOME at {cfg.data_swarm_home}")
    print("Next steps: set OPENAI_API_KEY in ~/.data_swarm/.env or shell env.")


def _cmd_task_new(args: argparse.Namespace) -> None:
    cfg = load_config()
    task = Task(task_id=str(uuid.uuid4())[:8], title=args.title, description=args.description, task_type=args.task_type)
    store = TaskStore(cfg.data_swarm_home)
    store.create(task)
    print(task.task_id)


def _cmd_task_run(args: argparse.Namespace) -> None:
    cfg = load_config()
    run_task(args.task_id, cfg.payload, cfg.data_swarm_home)


def _cmd_task_status(args: argparse.Namespace) -> None:
    cfg = load_config()
    task = TaskStore(cfg.data_swarm_home).load(args.task_id)
    print(f"{task.task_id}: {task.state.value}")


def _cmd_index_build(_: argparse.Namespace) -> None:
    cfg = load_config()
    idx = cfg.data_swarm_home / "indexes" / "meridian" / "index.sqlite"
    paths = cfg.payload["paths"]
    build_index(idx, [Path(paths["meridian_repo"]), Path(paths["meridian_aux_repo"])])
    print(f"Index built at {idx}")


def main() -> None:
    """Run CLI."""
    parser = argparse.ArgumentParser(prog="data-swarm")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    task = sub.add_parser("task")
    task_sub = task.add_subparsers(dest="task_cmd", required=True)
    new = task_sub.add_parser("new")
    new.add_argument("--title", required=True)
    new.add_argument("--description", required=True)
    new.add_argument("--task-type", default="general")
    run = task_sub.add_parser("run")
    run.add_argument("task_id")
    status = task_sub.add_parser("status")
    status.add_argument("task_id")

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
    elif args.cmd == "index" and args.index_cmd == "build":
        _cmd_index_build(args)


if __name__ == "__main__":
    main()
