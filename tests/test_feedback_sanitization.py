from pathlib import Path

from data_swarm.tools.anonymize import Anonymizer
from data_swarm.tools.io import FakeIO


def test_anonymizer_replaces_email_with_persona_token(tmp_path: Path) -> None:
    kb = tmp_path / "personas.yaml"
    kb.write_text("personas: []\n", encoding="utf-8")
    io = FakeIO(answers=["JD | Director | AgencyX | UK"])
    anonymizer = Anonymizer(kb)
    sanitized, used = anonymizer.collect_from_text("Discussed with jane@example.com about timeline.", io)
    assert "jane@example.com" not in sanitized
    assert "[JD | Director | AgencyX | UK]" in sanitized
    assert "JD | Director | AgencyX | UK" in used
