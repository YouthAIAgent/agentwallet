"""Tests for agent_genesis.breeder.evolution.BreederAgent."""

from __future__ import annotations

import random

from agent_genesis.breeder.evolution import BreederAgent, Genome


def make_base() -> Genome:
    return Genome(
        agent_id="scout_base",
        role="scout",
        system_prompt="You are a research scout. Find and verify information.",
        tool_config={"web_search": {"enabled": True}},
        model_params={"temperature": 0.7},
    )


def test_initialize_population(isolated_memory):
    b = BreederAgent()
    pop = b.initialize_population("scout", make_base(), size=10)
    assert len(pop) == 10
    assert pop[0].agent_id == "scout_base"
    assert all(g.role == "scout" for g in pop)


def test_evolve_returns_champion(isolated_memory):
    random.seed(42)
    b = BreederAgent()
    b.initialize_population("scout", make_base(), size=6)
    b.load_golden_set(
        "scout",
        [
            {"input": "find AI funding news", "expected": "list"},
            {"input": "monitor reddit", "expected": "summary"},
        ],
    )

    champion = b.evolve("scout", generations=3, population_size=6)

    assert champion.fitness > 0
    assert champion.generation >= 1
    # Champion persisted to memory
    saved = b.get_champion("scout")
    assert saved is not None
    assert saved.agent_id == champion.agent_id


def test_evolve_requires_population(isolated_memory):
    b = BreederAgent()
    b.load_golden_set("scout", [{"input": "x", "expected": "y"}])
    try:
        b.evolve("scout", generations=1, population_size=4)
    except ValueError as exc:
        assert "not initialized" in str(exc)
    else:
        raise AssertionError("expected ValueError for missing population")


def test_crossover_and_mutation_keep_role(isolated_memory):
    b = BreederAgent()
    p1 = make_base()
    p2 = Genome(
        agent_id="scout_v2",
        role="scout",
        system_prompt="You are an analyst. Compare things.",
        tool_config={"web_search": {"enabled": True}, "sql_query": {"enabled": True}},
        model_params={"temperature": 0.3, "max_tokens": 2048},
    )

    child = b._crossover(p1, p2)
    assert child.role == "scout"
    # Tool configs merged from both parents
    assert "web_search" in child.tool_config

    random.seed(7)
    mutated = b._mutate(child, mutation_rate=1.0)
    assert mutated.role == "scout"
    assert mutated.mutations  # at least one mutation recorded


def test_champion_persistence_roundtrip(isolated_memory):
    b = BreederAgent()
    champion = make_base()
    champion.fitness = 0.9
    b._save_champion("scout", champion)

    loaded = b.get_champion("scout")
    assert loaded is not None
    assert loaded.fitness == 0.9
    assert "scout" in b.list_champions()
