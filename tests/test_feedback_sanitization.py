from data_swarm.tools.io import FakeIO
from data_swarm.tools.redaction import sanitize_feedback


def test_sanitize_feedback_replaces_email_with_role() -> None:
    io = FakeIO(answers=["Client Lead", ""])
    sanitized, roles = sanitize_feedback("Discussed with jane@example.com about timeline.", io)
    assert "jane@example.com" not in sanitized
    assert "[Client Lead]" in sanitized
    assert roles == {"Client Lead"}
