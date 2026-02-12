"""Tests for agent CRUD operations."""

import pytest


@pytest.mark.asyncio
async def test_create_agent(client):
    """Test creating a new agent."""
    resp = await client.post("/v1/agents", json={
        "name": "test-crud-agent",
        "description": "Agent for CRUD test",
        "capabilities": ["trading"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "test-crud-agent"
    assert data["status"] == "active"
    assert "id" in data
    assert data["default_wallet_id"] is not None


@pytest.mark.asyncio
async def test_list_agents(client, test_agent):
    """Test listing agents."""
    resp = await client.get("/v1/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_agent(client, test_agent):
    """Test retrieving a specific agent."""
    resp = await client.get(f"/v1/agents/{test_agent.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == test_agent.name


@pytest.mark.asyncio
async def test_get_agent_not_found(client):
    """Test retrieving a non-existent agent."""
    resp = await client.get("/v1/agents/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_agent(client, test_agent):
    """Test updating an agent."""
    resp = await client.patch(f"/v1/agents/{test_agent.id}", json={
        "description": "Updated description",
    })
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated description"


@pytest.mark.asyncio
async def test_create_agent_unauthenticated(unauthed_client):
    """Test creating an agent without auth should fail."""
    resp = await unauthed_client.post("/v1/agents", json={
        "name": "unauth-agent",
        "description": "Should fail",
    })
    assert resp.status_code == 401
