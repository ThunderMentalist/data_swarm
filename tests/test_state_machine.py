import pytest

from data_swarm.orchestrator.state_machine import InvalidTransitionError, transition
from data_swarm.orchestrator.task_models import TaskState


def test_allowed_transition() -> None:
    record = transition(TaskState.NEW, TaskState.TRIAGED, "ok", [])
    assert record.to_state == "TRIAGED"


def test_active_to_closed_allowed() -> None:
    record = transition(TaskState.NEW, TaskState.CLOSED, "ok", [])
    assert record.to_state == "CLOSED"


def test_invalid_transition() -> None:
    with pytest.raises(InvalidTransitionError):
        transition(TaskState.CLOSED, TaskState.DELIVERED, "bad", [])
