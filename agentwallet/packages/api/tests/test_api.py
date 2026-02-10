"""Integration tests for the AgentWallet API."""

import pytest
from httpx import ASGITransport, AsyncClient

from agentwallet.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    resp = await client.post("/v1/auth/register", json={
        "org_name": "Test Org",
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "org_id" in data
    token = data["access_token"]

    # Login
    resp = await client.post("/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    # Duplicate register
    resp = await client.post("/v1/auth/register", json={
        "org_name": "Test Org 2",
        "email": "test@example.com",
        "password": "testpass456",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_unauthenticated_access(client):
    resp = await client.get("/v1/agents")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_agents_crud(client):
    # Register to get token
    resp = await client.post("/v1/auth/register", json={
        "org_name": "Agent Test Org",
        "email": "agents@example.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create agent
    resp = await client.post("/v1/agents", json={
        "name": "trading-bot",
        "description": "A trading agent",
        "capabilities": ["trading", "payments"],
    }, headers=headers)
    assert resp.status_code == 201
    agent = resp.json()
    assert agent["name"] == "trading-bot"
    assert agent["default_wallet_id"] is not None
    agent_id = agent["id"]

    # List agents
    resp = await client.get("/v1/agents", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1

    # Get agent
    resp = await client.get(f"/v1/agents/{agent_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "trading-bot"

    # Update agent
    resp = await client.patch(f"/v1/agents/{agent_id}", json={
        "description": "Updated description",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated description"


@pytest.mark.asyncio
async def test_wallets(client):
    resp = await client.post("/v1/auth/register", json={
        "org_name": "Wallet Test Org",
        "email": "wallets@example.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create wallet
    resp = await client.post("/v1/wallets", json={
        "wallet_type": "treasury",
        "label": "Main Treasury",
    }, headers=headers)
    assert resp.status_code == 201
    wallet = resp.json()
    assert wallet["wallet_type"] == "treasury"
    assert wallet["address"]  # should have a Solana address
    assert len(wallet["address"]) > 30

    # List wallets
    resp = await client.get("/v1/wallets", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_policies_crud(client):
    resp = await client.post("/v1/auth/register", json={
        "org_name": "Policy Test Org",
        "email": "policies@example.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create policy
    resp = await client.post("/v1/policies", json={
        "name": "Spending Limit",
        "rules": {
            "spending_limit_lamports": 1000000000,
            "daily_limit_lamports": 5000000000,
        },
        "scope_type": "org",
        "priority": 10,
    }, headers=headers)
    assert resp.status_code == 201
    policy = resp.json()
    policy_id = policy["id"]

    # List policies
    resp = await client.get("/v1/policies", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    # Update policy
    resp = await client.patch(f"/v1/policies/{policy_id}", json={
        "enabled": False,
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False

    # Delete policy
    resp = await client.delete(f"/v1/policies/{policy_id}", headers=headers)
    assert resp.status_code == 200
