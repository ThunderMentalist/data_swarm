from data_swarm.orchestrator.hitl import ask_multiline
from data_swarm.tools.io import FakeIO


def test_ask_multiline_collects_lines_until_end() -> None:
    io = FakeIO(answers=["line1", "line2", "END"])
    result = ask_multiline(io, "Paste details")
    assert result == "line1\nline2"
