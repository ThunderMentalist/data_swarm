from pathlib import Path

from data_swarm.tools.dotenv import load_dotenv


def test_load_dotenv_sets_and_does_not_override(monkeypatch, tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=abc\n", encoding="utf-8")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    load_dotenv(env)
    assert "OPENAI_API_KEY" in __import__("os").environ
    assert __import__("os").environ["OPENAI_API_KEY"] == "abc"

    monkeypatch.setenv("OPENAI_API_KEY", "preset")
    load_dotenv(env)
    assert __import__("os").environ["OPENAI_API_KEY"] == "preset"
