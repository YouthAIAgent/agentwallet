"""Tests for agent_genesis.cli.genesis.GenesisCLI."""

from __future__ import annotations

import json

import pytest

from agent_genesis.cli.genesis import GenesisCLI


@pytest.fixture()
def cli(plugin_env):
    return GenesisCLI()


@pytest.mark.asyncio
async def test_no_args_prints_help(cli, capsys):
    await cli.run([])
    out = capsys.readouterr().out
    assert "Agent Genesis CLI" in out
    assert "design" in out


@pytest.mark.asyncio
async def test_design_command_prints_spec(cli, capsys):
    await cli.run(["design", "monitor tenders and draft a proposal"])
    out = capsys.readouterr().out
    assert '"agents"' in out
    assert '"id"' in out


@pytest.mark.asyncio
async def test_design_without_task_shows_usage(cli, capsys):
    await cli.run(["design"])
    out = capsys.readouterr().out
    assert "Usage: genesis design" in out


@pytest.mark.asyncio
async def test_design_with_runtime_constraint(cli, capsys):
    """--runtime role=runtime must force the designer's runtime choice."""
    await cli.run(
        [
            "design",
            "parse documents, validate compliance",
            "--runtime",
            "parser=local_llm",
        ]
    )
    out = capsys.readouterr().out
    spec = json.loads(out)
    parser = next(a for a in spec["agents"] if a["role"] == "parser")
    assert parser["runtime"] == "local_llm"


@pytest.mark.asyncio
async def test_unknown_command(cli, capsys):
    await cli.run(["frobnicate"])
    out = capsys.readouterr().out
    assert "Unknown command" in out


@pytest.mark.asyncio
async def test_memory_command(cli, capsys, isolated_memory):
    isolated_memory.remember("agent-a", "observation", "hello world")
    await cli.run(["memory", "hello"])
    out = capsys.readouterr().out
    assert '"episodic"' in out


@pytest.mark.asyncio
async def test_status_command(cli, capsys):
    await cli.run(["status"])
    out = capsys.readouterr().out
    assert "Memory:" in out
    assert "Runtimes:" in out


@pytest.mark.asyncio
async def test_status_shows_deployer_load(cli, capsys):
    """genesis status must expose active agents, peak, and the cap."""
    await cli.run(["status"])
    out = capsys.readouterr().out
    assert "Deployer:" in out
    assert "active agents" in out
    assert "peak" in out


@pytest.mark.asyncio
async def test_deployer_status_reports_real_load(isolated_memory):
    """genesis_deployer_status reflects the shared deployer instance."""
    from agent_genesis.plugins.hermes_genesis import genesis_deployer_status

    d = await genesis_deployer_status()
    assert "active_agents" in d
    assert "peak_concurrent" in d
    assert "max_concurrent_agents" in d
    assert d["max_concurrent_agents"] == 12
    assert d["active_agents"] == 0
    assert d["peak_concurrent"] == 0


@pytest.mark.asyncio
async def test_deployer_status_reads_shared_state(plugin_env, isolated_memory):
    """A state published by another process is what status reports."""
    from agent_genesis.plugins.hermes_genesis import genesis_deployer_status

    isolated_memory.set_state(
        "deployer",
        {"active_agents": 7, "peak_concurrent": 9, "max_concurrent_agents": 12},
    )
    d = await genesis_deployer_status()
    assert d["active_agents"] == 7
    assert d["peak_concurrent"] == 9


@pytest.mark.asyncio
async def test_deployer_publishes_state_on_deploy(plugin_env, isolated_memory, monkeypatch):
    """DeployAgent must publish live load to shared state on acquire/release."""
    import asyncio

    from agent_genesis.deployer.orchestrator import DeployerAgent

    class FakeProc:
        returncode = 0

        async def communicate(self, input=None):
            await asyncio.sleep(0.05)
            return b"done", b""

    async def fake_spawn(*cmd, **kwargs):
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_spawn)

    d = DeployerAgent(max_concurrent_agents=2)
    spec = {
        "id": "p1",
        "name": "P",
        "runtime": "codex",
        "model": "gpt-4o",
        "tools": [],
        "input_context": {"task": "x"},
        "output_contract": {},
    }
    await d.deploy_agent(spec, "dep-1")

    state = isolated_memory.get_state("deployer")
    assert state is not None
    assert state["active_agents"] == 0  # released after completion
    assert state["peak_concurrent"] >= 1
    assert state["max_concurrent_agents"] == 2
