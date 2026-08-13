"""Tests for agent_genesis.memory.fabric.MemoryFabric."""

from __future__ import annotations

from agent_genesis.memory import MemoryFabric


def make_memory(tmp_path):
    return MemoryFabric(tmp_path / "mem")


def test_remember_and_recall(tmp_path):
    m = make_memory(tmp_path)
    m.remember("agent-a", "observation", "found a lead", task_id="t1")
    m.remember("agent-b", "error", "timeout", task_id="t1")

    by_agent = m.recall(agent_id="agent-a")
    assert len(by_agent) == 1
    assert by_agent[0]["content"] == "found a lead"

    by_task = m.recall(task_id="t1", limit=10)
    assert len(by_task) == 2

    by_type = m.recall(event_type="error")
    assert len(by_type) == 1
    assert by_type[0]["event_type"] == "error"


def test_learn_and_query_facts(tmp_path):
    m = make_memory(tmp_path)
    m.learn_fact("GST", "GST is 18% in India", confidence=0.9)
    m.learn_fact("GST", "GST is 5% in UAE", confidence=0.4)

    hits = m.query_facts(concept="gst", min_conf=0.5)
    assert len(hits) == 1
    assert hits[0]["fact"] == "GST is 18% in India"

    all_hits = m.query_facts(concept="gst")
    assert len(all_hits) == 2


def test_learn_and_get_skill(tmp_path):
    m = make_memory(tmp_path)
    steps = [{"tool": "echo", "params": {"text": "hi"}}]
    skill_id = m.learn_skill("agent-a", "echo", steps, description="say hi")

    skill = m.get_skill("echo")
    assert skill is not None
    assert skill["id"] == skill_id
    assert skill["description"] == "say hi"

    # Skill success-rate tracking
    m.record_skill_result(skill_id, True)
    m.record_skill_result(skill_id, True)
    m.record_skill_result(skill_id, False)
    skill = m.get_skill("echo")
    assert skill["execution_count"] == 3
    assert 0.6 <= skill["success_rate"] <= 0.7

    assert len(m.list_skills()) == 1


def test_orgs_save_load_list(tmp_path):
    m = make_memory(tmp_path)
    spec = {"id": "org-1", "name": "test-org", "agents": []}
    m.save_org("org-1", spec)

    assert m.load_org("org-1") == spec
    assert m.load_org("nope") is None

    listed = m.list_orgs()
    assert len(listed) == 1
    assert listed[0]["id"] == "org-1"


def test_keyword_search(tmp_path):
    m = make_memory(tmp_path)
    m.remember("agent-a", "observation", "GST compliance report drafted")
    m.learn_fact("compliance", "deadline is Friday")

    results = m.keyword_search("gst compliance")
    assert len(results) >= 1
    kinds = {r["kind"] for r in results}
    assert "episodic" in kinds


def test_stats(tmp_path):
    m = make_memory(tmp_path)
    m.remember("agent-a", "observation", "x")
    m.learn_fact("c", "f")
    m.learn_skill("agent-a", "s", [{"tool": "t"}])
    m.save_org("org", {"id": "org"})

    stats = m.stats()
    assert stats["episodic"] == 1
    assert stats["semantic"] == 1
    assert stats["procedural"] == 1
    assert stats["orgs"] == 1


def test_recent_failures(tmp_path):
    m = make_memory(tmp_path)
    m.remember("agent-a", "observation", "ok")
    m.remember("agent-a", "error", "boom")
    m.remember("agent-a", "correction", "fixed it")

    fails = m.recent_failures(hours=24)
    assert len(fails) == 2
    assert all(f["event_type"] in ("error", "failure", "correction", "human_feedback") for f in fails)
