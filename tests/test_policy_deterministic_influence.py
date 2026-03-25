from data_swarm.stages.comms.critic import CommsCriticAgent
from data_swarm.stages.policy_store import PolicyPack


def test_policy_forbidden_word_changes_critic_output() -> None:
    critic = CommsCriticAgent()
    policy = PolicyPack(core_prompt="forbidden: guaranteed", behaviour_cards=[], decision_trees=[])
    final = {"channels": [{"channel": "email", "draft": "This is guaranteed to work."}]}
    eval_payload = critic.evaluate({}, final, policy)
    assert any("guaranteed" in gap for gap in eval_payload["gaps"])
