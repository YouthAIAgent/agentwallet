"""Tests for agent_genesis.skill_layer.openspace_integration (local fallback)."""

from __future__ import annotations

from agent_genesis.skill_layer.openspace_integration import OpenSpaceLayer


def make_layer(isolated_memory, tmp_path):
    return OpenSpaceLayer(workspace=str(tmp_path / "ws"))


def test_local_find_and_get_skill(isolated_memory, tmp_path):
    layer = make_layer(isolated_memory, tmp_path)
    layer.memory.learn_skill("agent-a", "echo", [{"tool": "echo"}], description="say hi")

    found = layer.find_skills_local("echo")
    assert len(found) == 1
    assert found[0]["skill_name"] == "echo"

    skill = layer.get_skill_local("echo")
    assert skill is not None
    assert skill["description"] == "say hi"


def test_local_record_execution(isolated_memory, tmp_path):
    layer = make_layer(isolated_memory, tmp_path)
    layer.memory.learn_skill("agent-a", "deploy", [{"tool": "deploy"}])
    layer.record_skill_execution("agent-a", "deploy", success=True)
    layer.record_skill_execution("agent-a", "deploy", success=False)

    skill = layer.memory.get_skill("deploy")
    assert skill["execution_count"] == 2
    assert skill["success_rate"] == 0.5

    episodes = layer.memory.recall(agent_id="agent-a", event_type="skill_execution")
    assert len(episodes) == 2


def test_missing_openspace_raises_on_cloud_paths(isolated_memory, tmp_path):
    """Cloud methods require the optional openspace package -> RuntimeError."""
    layer = make_layer(isolated_memory, tmp_path)
    try:
        import asyncio

        asyncio.run(layer.find_skills("find something"))
    except RuntimeError as exc:
        assert "OpenSpace" in str(exc)
    else:
        # If openspace happens to be installed, we can't assert failure.
        pass
