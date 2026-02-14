"""Tests for policy management operations."""

import pytest


@pytest.mark.asyncio
async def test_create_policy(client, test_agent):
    """Test creating a new policy."""
    resp = await client.post(
        "/v1/policies",
        json={
            "name": "Test Spending Limit",
            "rules": {
                "spending_limit_lamports": 1_000_000_000,
                "daily_limit_lamports": 5_000_000_000,
            },
            "scope_type": "agent",
            "scope_id": str(test_agent.id),
            "priority": 10,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Spending Limit"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_policies(client, test_policy):
    """Test listing policies."""
    resp = await client.get("/v1/policies")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_policy(client, test_policy):
    """Test retrieving a specific policy."""
    resp = await client.get(f"/v1/policies/{test_policy.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == test_policy.name


@pytest.mark.asyncio
async def test_update_policy(client, test_policy):
    """Test updating a policy."""
    resp = await client.patch(
        f"/v1/policies/{test_policy.id}",
        json={
            "enabled": False,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


@pytest.mark.asyncio
async def test_delete_policy(client, test_policy):
    """Test deleting a policy."""
    resp = await client.delete(f"/v1/policies/{test_policy.id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_policies_unauthenticated(unauthed_client):
    """Test accessing policies without auth should fail."""
    resp = await unauthed_client.get("/v1/policies")
    assert resp.status_code == 401
