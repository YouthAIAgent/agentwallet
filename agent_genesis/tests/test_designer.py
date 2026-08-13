"""Tests for agent_genesis.designer.architect.DesignerAgent."""

from __future__ import annotations

from agent_genesis.designer.architect import (
    AgentRole,
    DesignerAgent,
    OrganizationSpec,
    RuntimeTarget,
    _env_runtime_prefs,
)


def test_env_runtime_prefs_parsing(monkeypatch):
    monkeypatch.setenv("GENESIS_RUNTIME_PREFS", "parser=local_llm, validator=local_llm, ")
    prefs = _env_runtime_prefs()
    assert prefs == {"parser": "local_llm", "validator": "local_llm"}

    monkeypatch.delenv("GENESIS_RUNTIME_PREFS", raising=False)
    assert _env_runtime_prefs() == {}


def test_design_builds_valid_spec(isolated_memory):
    d = DesignerAgent()
    spec = d.design("Monitor GeM tenders, parse PDF requirements, draft proposal, validate compliance")

    assert isinstance(spec, OrganizationSpec)
    assert spec.id
    assert spec.agents, "expected at least one agent"
    assert spec.entry_points, "expected at least one entry point"

    roles = {a.role for a in spec.agents}
    assert AgentRole.SCOUT in roles  # "monitor" maps to scout
    assert AgentRole.PARSER in roles  # "parse" maps to parser
    assert AgentRole.WRITER in roles  # "draft" maps to writer
    assert AgentRole.VALIDATOR in roles  # "validate" maps to validator

    for a in spec.agents:
        assert a.runtime in RuntimeTarget
        assert a.model
        assert a.tools
        assert a.input_contract and a.output_contract

    # Topology references only known agents
    known = {a.id for a in spec.agents}
    for deps in spec.topology.values():
        assert set(deps) <= known


def test_design_persists_to_memory(isolated_memory):
    d = DesignerAgent()
    spec = d.design("analyze market data and write a report")

    saved = isolated_memory.load_org(spec.id)
    assert saved is not None
    assert saved["id"] == spec.id

    episodes = isolated_memory.recall(agent_id="designer", event_type="design")
    assert len(episodes) == 1


def test_design_respects_runtime_prefs(isolated_memory):
    d = DesignerAgent()
    spec = d.design("search for funding news", constraints={"runtime_prefs": {"scout": "box"}})

    scout = next(a for a in spec.agents if a.role == AgentRole.SCOUT)
    assert scout.runtime == RuntimeTarget.BOX


def test_role_keyword_mapping(isolated_memory):
    d = DesignerAgent()
    # No keyword match falls back to ANALYZER
    spec = d.design("something completely unrelated")
    assert all(a.role in (AgentRole.ANALYZER,) for a in spec.agents)
