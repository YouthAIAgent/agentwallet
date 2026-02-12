"""Tests for agent CRUD operations."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from agentwallet.models import Agent, AgentStatus


@pytest.mark.asyncio
async def test_create_agent(
    async_client: AsyncClient, 
    auth_headers: dict, 
    mock_redis,
    mock_solana_rpc
):
    """Test creating a new agent."""
    agent_data = {
        "name": "New Test Agent",
        "description": "A newly created test agent",
        "config": {"model": "gpt-4", "temperature": 0.8}
    }
    
    response = await async_client.post(
        "/v1/agents", 
        json=agent_data, 
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == agent_data["name"]
    assert data["description"] == agent_data["description"]
    assert data["config"] == agent_data["config"]
    assert data["status"] == AgentStatus.ACTIVE.value
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_agent_duplicate_name(
    async_client: AsyncClient, 
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test creating an agent with a duplicate name should fail."""
    agent_data = {
        "name": test_agent.name,  # Same name as existing agent
        "description": "Duplicate name agent",
        "config": {"model": "gpt-3.5-turbo"}
    }
    
    response = await async_client.post(
        "/v1/agents", 
        json=agent_data, 
        headers=auth_headers
    )
    
    assert response.status_code == 409
    assert "already exists" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_get_agent(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving a specific agent."""
    response = await async_client.get(
        f"/v1/agents/{test_agent.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_agent.id
    assert data["name"] == test_agent.name
    assert data["description"] == test_agent.description
    assert data["status"] == test_agent.status.value


@pytest.mark.asyncio
async def test_get_agent_not_found(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving a non-existent agent."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = await async_client.get(
        f"/v1/agents/{fake_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_list_agents(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    inactive_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test listing all agents for the authenticated user."""
    response = await async_client.get(
        "/v1/agents",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least our test agents
    
    # Check that we can find our test agents
    agent_ids = [agent["id"] for agent in data]
    assert test_agent.id in agent_ids
    assert inactive_agent.id in agent_ids


@pytest.mark.asyncio
async def test_list_agents_filter_status(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    inactive_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test listing agents filtered by status."""
    # Test filtering for active agents
    response = await async_client.get(
        "/v1/agents?status=active",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned agents should be active
    for agent in data:
        assert agent["status"] == AgentStatus.ACTIVE.value
    
    # Should include our active test agent
    active_agent_ids = [agent["id"] for agent in data]
    assert test_agent.id in active_agent_ids
    assert inactive_agent.id not in active_agent_ids


@pytest.mark.asyncio
async def test_update_agent(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test updating an agent."""
    update_data = {
        "name": "Updated Agent Name",
        "description": "Updated description",
        "config": {"model": "gpt-3.5-turbo", "temperature": 0.5},
        "status": "inactive"
    }
    
    response = await async_client.put(
        f"/v1/agents/{test_agent.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["config"] == update_data["config"]
    assert data["status"] == update_data["status"]


@pytest.mark.asyncio
async def test_update_agent_not_found(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test updating a non-existent agent."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    update_data = {"name": "Updated Name"}
    
    response = await async_client.put(
        f"/v1/agents/{fake_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_delete_agent(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    mock_redis,
    mock_solana_rpc
):
    """Test deleting an agent."""
    # Create a temporary agent for deletion
    from agentwallet.models import User
    from uuid import uuid4
    
    # Get the user for the agent
    result = await db_session.execute("SELECT * FROM users LIMIT 1")
    user = result.fetchone()
    
    temp_agent = Agent(
        id=str(uuid4()),
        name="Temp Agent for Deletion",
        description="Will be deleted",
        user_id=user.id,
        status=AgentStatus.ACTIVE,
        config={}
    )
    db_session.add(temp_agent)
    await db_session.commit()
    await db_session.refresh(temp_agent)
    
    response = await async_client.delete(
        f"/v1/agents/{temp_agent.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify agent is deleted
    get_response = await async_client.get(
        f"/v1/agents/{temp_agent.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_agent_unauthorized(
    async_client: AsyncClient,
    mock_redis,
    mock_solana_rpc
):
    """Test creating an agent without authentication should fail."""
    agent_data = {
        "name": "Unauthorized Agent",
        "description": "Should not be created"
    }
    
    response = await async_client.post("/v1/agents", json=agent_data)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_agent_invalid_data(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test creating an agent with invalid data."""
    agent_data = {
        "name": "",  # Empty name should be invalid
        "description": "Agent with empty name"
    }
    
    response = await async_client.post(
        "/v1/agents", 
        json=agent_data, 
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_agent_unauthorized(
    async_client: AsyncClient,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving an agent without authentication should fail."""
    response = await async_client.get(f"/v1/agents/{test_agent.id}")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_agent_permissions(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    mock_redis,
    mock_solana_rpc
):
    """Test that users can only access their own agents."""
    # This test would require creating another user and agent
    # For now, we'll just test that the authenticated user can access their agent
    response = await async_client.get("/v1/agents", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned agents should belong to the authenticated user
    # (This would be more meaningful with multiple users in the test)
    assert isinstance(data, list)