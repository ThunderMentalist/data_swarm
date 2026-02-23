import pytest

from data_swarm.orchestrator.state_machine import InvalidTransitionError, transition
from data_swarm.orchestrator.task_models import TaskState


def test_allowed_transition() -> None:
    record = transition(TaskState.NEW, TaskState.PLANNED, "ok", [])
    assert record.to_state == "PLANNED"


def test_invalid_transition() -> None:
    with pytest.raises(InvalidTransitionError):
        transition(TaskState.NEW, TaskState.CLOSED, "bad", [])
