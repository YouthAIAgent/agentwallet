"""Tests for agent_genesis.deployer.orchestrator.DeployerAgent."""

from __future__ import annotations

import asyncio
import sys

import pytest

from agent_genesis.deployer.orchestrator import (
    DEFAULT_MAX_CONCURRENT_AGENTS,
    DeployerAgent,
    RuntimeType,
    _exec_cmd,
)


def test_exec_cmd_wraps_windows_shims(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert _exec_cmd(["codex", "exec"]) == ["cmd", "/c", "codex", "exec"]
    monkeypatch.setattr(sys, "platform", "linux")
    assert _exec_cmd(["codex", "exec"]) == ["codex", "exec"]


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
async def test_codex_deploy_adds_provider_flag(isolated_memory, monkeypatch):
    monkeypatch.setenv("GENESIS_CODEX_PROVIDER", "omniroute")

    captured = {}

    class FakeProc:
        returncode = 0

        async def communicate(self, input=None):
            return b"done", b""

    async def fake_spawn(*cmd, **kwargs):
        captured["cmd"] = list(cmd)
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_spawn)

    d = DeployerAgent()
    spec = {
        "id": "a0",
        "name": "Validator",
        "runtime": "codex",
        "model": "oc/deepseek-v4-flash-free",
        "tools": [],
        "input_context": {"task": "validate"},
        "output_contract": {},
    }
    result = await d._deploy_codex(spec, "dep-1")

    assert result["status"] == "completed"
    assert "model_provider=omniroute" in captured["cmd"]
    assert "oc/deepseek-v4-flash-free" in captured["cmd"]


@pytest.mark.asyncio
async def test_codex_deploy_without_provider_keeps_args(isolated_memory, monkeypatch):
    monkeypatch.delenv("GENESIS_CODEX_PROVIDER", raising=False)

    captured = {}

    class FakeProc:
        returncode = 0

        async def communicate(self, input=None):
            return b"done", b""

    async def fake_spawn(*cmd, **kwargs):
        captured["cmd"] = list(cmd)
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_spawn)

    d = DeployerAgent()
    spec = {
        "id": "a0",
        "name": "Validator",
        "runtime": "codex",
        "model": "gpt-4o",
        "tools": [],
        "input_context": {"task": "validate"},
        "output_contract": {},
    }
    await d._deploy_codex(spec, "dep-1")

    assert "model_provider=omniroute" not in captured["cmd"]
    assert "gpt-4o" in captured["cmd"]


def test_default_concurrency_cap(isolated_memory):
    d = DeployerAgent()
    assert d.max_concurrent_agents == DEFAULT_MAX_CONCURRENT_AGENTS
    assert DEFAULT_MAX_CONCURRENT_AGENTS == 12


def test_concurrency_cap_from_env(isolated_memory, monkeypatch):
    monkeypatch.setenv("GENESIS_MAX_CONCURRENT_AGENTS", "7")
    d = DeployerAgent()
    assert d.max_concurrent_agents == 7


def test_concurrency_cap_constructor_wins(isolated_memory, monkeypatch):
    monkeypatch.setenv("GENESIS_MAX_CONCURRENT_AGENTS", "99")
    d = DeployerAgent(max_concurrent_agents=4)
    assert d.max_concurrent_agents == 4


@pytest.mark.asyncio
async def test_deploy_agent_never_exceeds_cap(isolated_memory, monkeypatch):
    """Cap=2 -> at most 2 agents run simultaneously even when 6 are fanned out."""
    captured = {"running": 0, "peak": 0}

    class FakeProc:
        returncode = 0

        async def communicate(self, input=None):
            captured["running"] += 1
            captured["peak"] = max(captured["peak"], captured["running"])
            await asyncio.sleep(0.05)
            captured["running"] -= 1
            return b"done", b""

    async def fake_spawn(*cmd, **kwargs):
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_spawn)

    d = DeployerAgent(max_concurrent_agents=2)
    specs = [
        {
            "id": f"a{i}",
            "name": "Agent",
            "runtime": "codex",
            "model": "gpt-4o",
            "tools": [],
            "input_context": {"task": "x"},
            "output_contract": {},
        }
        for i in range(6)
    ]
    await asyncio.gather(*(d.deploy_agent(s, "dep-1") for s in specs))

    assert captured["peak"] <= 2
    assert d.peak_concurrent <= 2
    assert d.active_agent_count == 0


@pytest.mark.asyncio
async def test_deploy_organization_respects_cap(isolated_memory, monkeypatch):
    """Org with many independent agents still respects the cap."""
    captured = {"running": 0, "peak": 0}

    class FakeProc:
        returncode = 0

        async def communicate(self, input=None):
            captured["running"] += 1
            captured["peak"] = max(captured["peak"], captured["running"])
            await asyncio.sleep(0.03)
            captured["running"] -= 1
            return b"done", b""

    async def fake_spawn(*cmd, **kwargs):
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_spawn)

    d = DeployerAgent(max_concurrent_agents=3)
    org = {
        "agents": [
            {
                "id": f"a{i}",
                "name": "Agent",
                "runtime": "codex",
                "model": "gpt-4o",
                "tools": [],
                "input_context": {"task": "x"},
                "output_contract": {},
                "depends_on": [],
            }
            for i in range(8)
        ]
    }
    result = await d.deploy_organization(org)

    assert result["status"] == "completed"
    assert len(result["agents"]) == 8
    assert captured["peak"] <= 3


@pytest.mark.asyncio
async def test_deploy_organization_respects_dependencies(isolated_memory, monkeypatch):
    """Dependent agent only runs after its dependency completes."""
    order = []

    class FakeProc:
        returncode = 0

        async def communicate(self, input=None):
            await asyncio.sleep(0.02)
            return b"done", b""

    async def fake_spawn(*cmd, **kwargs):
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_spawn)

    d = DeployerAgent(max_concurrent_agents=1)

    async def deploy_id(agent_id):
        order.append(agent_id)
        # intercept only the agent under test; others go through normally
        result = await d.deploy_agent(
            {
                "id": agent_id,
                "name": "Agent",
                "runtime": "codex",
                "model": "gpt-4o",
                "tools": [],
                "input_context": {"task": "x"},
                "output_contract": {},
            },
            "dep-1",
        )
        return result

    # Patch deploy_agent to record order (monkeypatch on instance)
    original = d.deploy_agent

    async def recording_deploy(spec, deployment_id):
        order.append(spec["id"])
        return await original(spec, deployment_id)

    monkeypatch.setattr(d, "deploy_agent", recording_deploy)

    org = {
        "agents": [
            {"id": "a0", "name": "A", "runtime": "codex", "model": "m", "tools": [], "input_context": {}, "output_contract": {}, "depends_on": []},
            {"id": "a1", "name": "B", "runtime": "codex", "model": "m", "tools": [], "input_context": {}, "output_contract": {}, "depends_on": ["a0"]},
        ]
    }
    await d.deploy_organization(org)

    assert order.index("a0") < order.index("a1")


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
