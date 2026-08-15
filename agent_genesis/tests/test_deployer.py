"""Tests for agent_genesis.deployer.orchestrator.DeployerAgent."""

from __future__ import annotations

import asyncio
import sys

import pytest

from agent_genesis.deployer.orchestrator import (
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
