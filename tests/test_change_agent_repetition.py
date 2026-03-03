import pytest

from data_swarm.stages.comms.change import CommsChangeAgent
from data_swarm.stages.navigation.change import NavigationChangeAgent
from data_swarm.stages.planner.change import PlannerChangeAgent
from data_swarm.stages.stakeholder.change import StakeholderChangeAgent


@pytest.mark.parametrize(
    "stage_key,agent",
    [
        ("planner", PlannerChangeAgent()),
        ("stakeholder", StakeholderChangeAgent()),
        ("navigation", NavigationChangeAgent()),
        ("comms", CommsChangeAgent()),
    ],
)
def test_change_agent_repetition_signals(tmp_path, stage_key: str, agent) -> None:
    home = tmp_path / ".data_swarm"
    home.mkdir()
    critic = {
        "suggestions": [
            {
                "title": f"{stage_key} suggestion",
                "rationale": "r",
                "evidence": "e",
                "suggestion_key": f"{stage_key}_suggestion",
            }
        ]
    }
    agent.generate("t1", critic, {"facts": ["f"]}, home)
    second = agent.generate("t2", critic, {"facts": ["f"]}, home)
    assert "becoming repetitive" in second
