"""Tests for Agent Swarm endpoints."""

import uuid

import pytest

from agentwallet.models import Agent


@pytest.fixture
async def worker_agent(db_session, test_org):
    agent = Agent(
        org_id=test_org.id,
        name="Worker Agent",
        description="A worker agent for swarm testing",
        status="active",
        capabilities=["data-processing"],
        is_public=True,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.fixture
async def swarm(client, test_agent):
    """Create a swarm and return the response data."""
    resp = await client.post(
        "/v1/swarms",
        json={
            "name": "Test Research Swarm",
            "description": "A swarm for testing",
            "orchestrator_agent_id": str(test_agent.id),
            "swarm_type": "research",
            "max_members": 5,
        },
    )
    assert resp.status_code == 200
    return resp.json()


# ── Swarm CRUD ──


@pytest.mark.asyncio
async def test_create_swarm(client, test_agent):
    resp = await client.post(
        "/v1/swarms",
        json={
            "name": "Trading Swarm",
            "description": "A trading swarm cluster",
            "orchestrator_agent_id": str(test_agent.id),
            "swarm_type": "trading",
            "max_members": 10,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Trading Swarm"
    assert data["swarm_type"] == "trading"
    assert data["member_count"] == 1  # Orchestrator auto-added
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_swarms(client, swarm):
    resp = await client.get("/v1/swarms")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_swarm(client, swarm):
    resp = await client.get(f"/v1/swarms/{swarm['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == swarm["id"]
    assert data["member_count"] >= 1


# ── Members ──


@pytest.mark.asyncio
async def test_add_member(client, swarm, worker_agent):
    resp = await client.post(
        f"/v1/swarms/{swarm['id']}/members",
        json={
            "agent_id": str(worker_agent.id),
            "role": "worker",
            "specialization": "data-analysis",
            "is_contestable": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "worker"
    assert data["specialization"] == "data-analysis"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_members(client, swarm, worker_agent):
    # Add worker first
    await client.post(
        f"/v1/swarms/{swarm['id']}/members",
        json={"agent_id": str(worker_agent.id), "role": "worker"},
    )
    resp = await client.get(f"/v1/swarms/{swarm['id']}/members")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2  # Orchestrator + worker


@pytest.mark.asyncio
async def test_remove_member(client, swarm, worker_agent):
    # Add then remove
    await client.post(
        f"/v1/swarms/{swarm['id']}/members",
        json={"agent_id": str(worker_agent.id), "role": "worker"},
    )
    resp = await client.delete(f"/v1/swarms/{swarm['id']}/members/{worker_agent.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "removed"


# ── Tasks ──


@pytest.mark.asyncio
async def test_create_task(client, swarm):
    resp = await client.post(
        f"/v1/swarms/{swarm['id']}/tasks",
        json={
            "title": "Analyze DeFi market",
            "description": "Research top 20 DeFi protocols",
            "task_type": "research",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Analyze DeFi market"
    assert data["status"] == "pending"
    assert data["total_subtasks"] == 0


@pytest.mark.asyncio
async def test_list_tasks(client, swarm):
    await client.post(
        f"/v1/swarms/{swarm['id']}/tasks",
        json={"title": "Task for listing", "description": "Test list"},
    )
    resp = await client.get(f"/v1/swarms/{swarm['id']}/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_task(client, swarm):
    create_resp = await client.post(
        f"/v1/swarms/{swarm['id']}/tasks",
        json={"title": "Get this task", "description": "Test get"},
    )
    task_id = create_resp.json()["id"]
    resp = await client.get(f"/v1/swarms/{swarm['id']}/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_assign_subtask(client, swarm, worker_agent):
    # Add worker to swarm
    await client.post(
        f"/v1/swarms/{swarm['id']}/members",
        json={"agent_id": str(worker_agent.id), "role": "worker"},
    )
    # Create task
    task_resp = await client.post(
        f"/v1/swarms/{swarm['id']}/tasks",
        json={"title": "Decompose this", "description": "Multi-step task"},
    )
    task_id = task_resp.json()["id"]

    # Assign subtask
    resp = await client.post(
        f"/v1/swarms/{swarm['id']}/tasks/{task_id}/assign",
        json={
            "subtask_id": "sub-1",
            "agent_id": str(worker_agent.id),
            "description": "Analyze token prices",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "in_progress"
    assert data["total_subtasks"] == 1
    assert len(data["subtasks"]) == 1
    assert data["subtasks"][0]["id"] == "sub-1"


@pytest.mark.asyncio
async def test_complete_subtask_auto_aggregation(client, swarm, worker_agent):
    # Add worker
    await client.post(
        f"/v1/swarms/{swarm['id']}/members",
        json={"agent_id": str(worker_agent.id), "role": "worker"},
    )
    # Create task
    task_resp = await client.post(
        f"/v1/swarms/{swarm['id']}/tasks",
        json={"title": "Auto-aggregate test", "description": "Should auto-complete"},
    )
    task_id = task_resp.json()["id"]

    # Assign one subtask
    await client.post(
        f"/v1/swarms/{swarm['id']}/tasks/{task_id}/assign",
        json={
            "subtask_id": "sub-agg",
            "agent_id": str(worker_agent.id),
            "description": "Do the work",
        },
    )

    # Complete it
    resp = await client.post(
        f"/v1/swarms/{swarm['id']}/tasks/{task_id}/complete",
        json={
            "subtask_id": "sub-agg",
            "result": {"output": "Analysis complete", "score": 95},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["completed_subtasks"] == 1
    assert data["aggregated_result"] is not None
    assert data["completed_at"] is not None


# ── Auth ──


@pytest.mark.asyncio
async def test_swarm_unauthenticated(unauthed_client):
    resp = await unauthed_client.get("/v1/swarms")
    assert resp.status_code == 401
