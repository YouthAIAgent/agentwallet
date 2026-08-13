"""Tests for agent_genesis.deployer.orchestrator.DeployerAgent."""

from __future__ import annotations

import pytest

from agent_genesis.deployer.orchestrator import DeployerAgent, RuntimeType


def test_runtime_configs_loaded(isolated_memory):
    d = DeployerAgent()
    for rt in RuntimeType:
        assert rt in d.runtime_configs


@pytest.mark.asyncio
async def test_deploy_empty_org(isolated_memory):
    d = DeployerAgent()
    result = await d.deploy_organization({"agents": []})
    assert result["status"] == "completed"
    assert result["agents"] == {}
    assert result["deployment_id"]


@pytest.mark.asyncio
async def test_deploy_box_without_token_fails_gracefully(isolated_memory, monkeypatch):
    d = DeployerAgent(box_token=None)
    result = await d.deploy_agent(
        {"id": "a0", "runtime": "box", "model": "claude-3-5-sonnet-20241022"},
        "dep-1",
    )
    assert result["status"] == "failed"
    assert "token" in result["error"].lower()


@pytest.mark.asyncio
async def test_deploy_hermes_offline_fails_gracefully(isolated_memory):
    """No Hermes server running -> deterministic 'failed' (no crash)."""
    d = DeployerAgent()
    result = await d.deploy_agent(
        {"id": "a0", "runtime": "hermes", "model": "qwen2.5:7b", "task": "x", "tools": []},
        "dep-1",
    )
    assert result["status"] == "failed"
    assert result["runtime"] == "hermes"


@pytest.mark.asyncio
async def test_deploy_organization_remembers(isolated_memory):
    d = DeployerAgent()
    await d.deploy_organization(
        {
            "agents": [
                {
                    "id": "a0",
                    "runtime": "box",
                    "model": "m",
                    "depends_on": [],
                    "tools": [],
                    "task": "",
                }
            ]
        }
    )
    episodes = isolated_memory.recall(agent_id="deployer", event_type="agent_deployed")
    assert len(episodes) == 1
    import json

    metadata = json.loads(episodes[0]["metadata"])
    assert metadata["deployment_id"]
