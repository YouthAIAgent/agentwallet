"""Tests for policy management operations."""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from agentwallet.models import Policy, Agent


@pytest.mark.asyncio
async def test_create_policy(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test creating a new policy for an agent."""
    policy_data = {
        "agent_id": test_agent.id,
        "name": "Daily Spending Limit",
        "rules": {
            "daily_spending_limit": "10.00",
            "max_transaction_amount": "5.00",
            "allowed_recipients": ["*"]
        },
        "is_active": True
    }
    
    response = await async_client.post(
        "/v1/policies",
        json=policy_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == test_agent.id
    assert data["name"] == "Daily Spending Limit"
    assert data["rules"] == policy_data["rules"]
    assert data["is_active"] == policy_data["is_active"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_policy_duplicate_name(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test creating a policy with a duplicate name should fail."""
    # First create a policy
    policy_data = {
        "agent_id": test_agent.id,
        "name": "Test Policy",
        "rules": {
            "daily_spending_limit": "10.00"
        },
        "is_active": True
    }
    response = await async_client.post("/v1/policies", json=policy_data, headers=auth_headers)
    assert response.status_code == 201
    
    # Try to create another policy with same name
    response = await async_client.post("/v1/policies", json=policy_data, headers= auth_headers)
    assert response.status_code == 409
    assert "already exists" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_list_policies(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    db_session: AsyncSession,
    mock_redis,
    mock_solana_rpc
):
    """Test listing all policies for the authenticated user."""
    # Create two test policies
    policy1 = Policy(
        id="policy1",
        agent_id=test_agent.id,
        name="Policy One",
        rules={"daily_spending_limit": "5.00"},
        is_active=True
    )
    policy2 = Policy(
        id="policy2",
        agent_id=test_agent.id,
        name="Policy Two",
        rules={"daily_spending_limit": "10.00"},
        is_active=False
    )
    db_session.add_all([policy1, policy2])
    await db_session.commit()
    await db_session.refresh(policy1)
    await db_session.refresh(policy2)
    
    response = await async_client.get(
        "/v1/policies",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(p["name"] == "Policy One" for p in data)
    assert any(p["name"] == "Policy Two" for p in data)


@pytest.mark.asyncio
async def test_update_policy(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test updating an existing policy."""
    # Create test policy
    policy = Policy(
        id="policy1",
        agent_id=test_agent.id,
        name="Original Policy",
        rules={"daily_spending_limit": "5.00"},
        is_active=True
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)
    
    update_data = {
        "name": "Updated Policy",
        "rules": {
            "daily_spending_limit": "7.50",
            "max_transaction_amount": "3.00"
        },
        "is_active": False
    }
    
    response = await async_client.put(
        f"/v1/policies/{policy.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["rules"] == update_data["rules"]
    assert data["is_active"] == update_data["is_active"]


@pytest.mark.asyncio
async def test_update_policy_not_found(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test updating a policy that doesn't exist."""
    response = await async_client.put(
        "/v1/policies/invalid-id",
        json={"name": "New Name"},
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_delete_policy(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test deleting a policy."""
    # Create policy
    policy = Policy(
        id="policy1",
        agent_id=test_agent.id,
        name="Test Policy",
        rules={"daily_spending_limit": "10.00"},
        is_active=False
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)
    
    # Delete policy
    response = await async_client.delete(
        f"/v1/policies/{policy.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify policy no longer exists
    response = await async_client.get(
        "/v1/policies",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert all(p["id"] != policy.id for p in data)

@pytest.mark.asyncio
async def test_delete_policy_not_found(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test deleting a non-existent policy."""
    response = await async_client.delete(
        "/v1/policies/invalid-id",
        headers=auth_headers
    )
    
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_policy_details(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving policy details."""
    # Create policy
    policy = Policy(
        id="policy1",
        agent_id=test_agent.id,
        name="Sample Policy",
        rules={
            "daily_spending_limit": "15.00",
            "allowed_recipients": ["solana:eBw9p6D5v14p912vKX81c9Jp4vE7p3g9h2X3j6vP9jK4"]
        },
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)
    
    response = await async_client.get(
        f"/v1/policies/{policy.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == policy.id
    assert data["name"] == policy.name
    assert data["rules"] == policy.rules
    assert data["is_active"] == policy.is_active

@pytest.mark.asyncio
async def test_get_policy_not_found(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving a non-existent policy."""
    response = await async_client.get(
        "/v1/policies/invalid-id",
        headers=auth_headers
    )
    
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_policy_validation(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test creating policy with invalid data."""
    # Test invalid daily spending limit (negative)
    response = await async_client.post(
        "/v1/policies",
        json={
            "name": "Invalid Policy",
            "rules": {
                "daily_spending_limit": "-5.00"
            },
            "is_active": True
        },
        headers=auth_headers
    )
    assert response.status_code == 422
    
    # Test invalid max transaction amount (0)
    response = await async_client.post(
        "/v1/policies",
        json={
            "name": "Zero Limit",
            "rules": {
                "max_transaction_amount": "0"
            },
            "is_active": True
        },
        headers=auth_headers
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_policy_application(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_agent: Agent,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test policy enforcement during transactions."""
    # Create a policy with spending limit
    policy = Policy(
        id="policy1",
        agent_id=test_agent.id,
        name="Spending Limit",
        rules={
            "daily_spending_limit": "0.01",
            "max_transaction_amount": "0.005"
        },
        is_active=True
    )
    db_session.add(policy)
    await db_session.commit()
    
    # Attempt to transfer exceeding daily limit
    transfer_data = {
        "from_wallet_id": test_wallet.id,
        "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "amount": "0.02",  # Total would exceed daily limit combined with 0.005
        "memo": "Should be denied"
    }
    
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 403
    assert "policy" in response.json()["error"].lower()
    
    # Attempt to transfer within limits
    transfer_data["amount"] = "0.005"
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert "solana_signature" in response.json()

@pytest.mark.asyncio
async def test_policy_deactivation(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test using policies with different active states."""
    # Create inactive policy
    inactive_policy = Policy(
        id="policy1",
        agent_id=test_agent.id,
        name="Inactive Policy",
        rules={"daily_spending_limit": "5.00"},
        is_active=False
    )
    db_session.add(inactive_policy)
    await db_session.commit()
    
    # Create active policy
    active_policy = Policy(
        id="policy2",
        agent_id=test_agent.id,
        name="Active Policy",
        rules={"daily_spending_limit": "0.01"},
        is_active=True
    )
    db_session.add(active_policy)
    await db_session.commit()
    
    # Attempt to transfer with active policy
    transfer_data = {
        "from_wallet_id": test_wallet.id,
        "to_address": "5Gv8eWrN7B9dqTCEKh8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "amount": "0.02"
    }
    
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    
    # Update policy to inactive
    response = await async_client.put(
        f"/v1/policies/{active_policy.id}",
        json={"is_active": False},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    # Should no longer be blocked after deactivation
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201