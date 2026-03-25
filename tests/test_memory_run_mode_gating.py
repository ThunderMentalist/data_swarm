import sqlite3
from pathlib import Path

from data_swarm.orchestrator.run_mode import RunMode, RunModePolicy
from data_swarm.orchestrator.task_models import Task
from data_swarm.stages.stakeholder.stage import StakeholderStage
from data_swarm.stores.log_store import LogStore
from data_swarm.stores.memory_store import MemoryStore
from data_swarm.stores.task_store import TaskStore
from data_swarm.tools.io import FakeIO


def _role_note_count(db_path: Path) -> int:
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM role_notes").fetchone()[0]


def test_memory_write_blocked_by_run_mode(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    (home / "kb").mkdir(parents=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    store = TaskStore(home)
    task = Task(task_id="m1", title="t", description="d")
    task_dir = store.create(task)
    io = FakeIO(answers=["END", "1"])
    stage = StakeholderStage(config={}, home=home, io=io, store=store, logs=LogStore(task_dir))
    memory = MemoryStore(home)
    deny = RunModePolicy(True, True, True, False, False, False, True, False, False)
    stage.run(task, task_dir, kb={}, memory_store=memory, run_mode=RunMode.INITIAL_USING, run_mode_policy=deny)
    assert _role_note_count(memory.path) == 0


def test_memory_write_enabled(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    (home / "kb").mkdir(parents=True)
    (home / "kb" / "personas.yaml").write_text("personas: []\n", encoding="utf-8")
    store = TaskStore(home)
    task = Task(task_id="m2", title="t", description="d")
    task_dir = store.create(task)
    io = FakeIO(answers=["END", "1"])
    stage = StakeholderStage(config={}, home=home, io=io, store=store, logs=LogStore(task_dir))
    memory = MemoryStore(home)
    allow = RunModePolicy(True, True, True, True, False, False, True, False, False)
    stage.run(task, task_dir, kb={}, memory_store=memory, run_mode=RunMode.INITIAL_USING, run_mode_policy=allow)
    assert _role_note_count(memory.path) >= 1
