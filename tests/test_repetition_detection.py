import json
from pathlib import Path

from data_swarm.stages.triage.change import TriageChangeAgent


def test_repetition_detection_increments_and_reports(tmp_path: Path) -> None:
    home = tmp_path / ".data_swarm"
    (home / "triage_policy" / "history").mkdir(parents=True, exist_ok=True)
    (home / "triage_policy" / "history" / "triage_change_requests.jsonl").touch()
    (home / "triage_policy" / "history" / "repetition_index.json").write_text("{}", encoding="utf-8")

    agent = TriageChangeAgent()
    critic_eval = {
        "suggestions": [
            {
                "title": "Use measurable success criteria",
                "rationale": "Improves quality",
                "evidence": "Observed in brief",
            }
        ]
    }
    curator_candidates = {"facts": ["fact"]}

    agent.generate("task-1", critic_eval, curator_candidates, home)
    output = agent.generate("task-2", critic_eval, curator_candidates, home)

    repetition_path = home / "triage_policy" / "history" / "repetition_index.json"
    repetition_index = json.loads(repetition_path.read_text(encoding="utf-8"))
    assert repetition_index["use_measurable_success_criteria"] == 2
    assert "Repetition signal: seen 2 times; becoming repetitive." in output
