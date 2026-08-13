"""Tests for agent_genesis.plugins.hermes_genesis tool functions."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_genesis_design(plugin_env):
    result = await plugin_env.genesis_design("monitor tenders and draft a proposal")
    assert result["status"] == "designed"
    spec = result["spec"]
    assert spec["id"]
    assert len(spec["agents"]) >= 1
    assert spec["entry_points"]


@pytest.mark.asyncio
async def test_genesis_design_and_load_org(plugin_env):
    designed = await plugin_env.genesis_design("analyze market data")
    org_id = designed["spec"]["id"]

    loaded = await plugin_env.genesis_load_org(org_id)
    assert loaded["status"] == "loaded"
    assert loaded["spec"]["id"] == org_id

    missing = await plugin_env.genesis_load_org("does-not-exist")
    assert missing["status"] == "not_found"


@pytest.mark.asyncio
async def test_genesis_list_orgs(plugin_env):
    await plugin_env.genesis_design("write a weekly report")
    orgs = await plugin_env.genesis_list_orgs()
    assert len(orgs["orgs"]) >= 1


@pytest.mark.asyncio
async def test_genesis_memory_stats(plugin_env):
    await plugin_env.genesis_design("find suppliers and draft emails")
    stats = await plugin_env.genesis_memory_stats()
    assert stats["episodic"] >= 1
    assert stats["orgs"] >= 1


@pytest.mark.asyncio
async def test_genesis_breed_end_to_end(plugin_env):
    await plugin_env.genesis_load_golden(
        "scout",
        [
            {"input": "find AI funding news", "expected": "list"},
            {"input": "monitor reddit for agent chatter", "expected": "summary"},
        ],
    )
    result = await plugin_env.genesis_breed(
        "scout",
        generations=2,
        population_size=5,
        base_prompt="You are a research scout. Find and verify information.",
    )
    assert result["status"] == "evolved"
    champion = result["champion"]
    assert champion["fitness"] > 0


@pytest.mark.asyncio
async def test_genesis_breed_requires_golden_set(plugin_env):
    result = await plugin_env.genesis_breed("scout", generations=1, population_size=4)
    assert result["status"] == "error"
    assert "golden" in result["message"].lower()


@pytest.mark.asyncio
async def test_openspace_local_fallback_tools(plugin_env):
    plugin_env._openspace.memory.learn_skill(
        "agent-a", "echo", [{"tool": "echo"}], description="say hi"
    )
    recorded = await plugin_env.openspace_local_record("agent-a", "echo", True)
    assert recorded["status"] == "recorded"

    skills = await plugin_env.openspace_local_search("echo")
    assert len(skills["skills"]) == 1

    skill = await plugin_env.openspace_local_skill("echo")
    assert skill["skill"]["description"] == "say hi"
