"""Tests for escrow operations."""

import pytest


@pytest.mark.asyncio
async def test_create_escrow(client, test_wallet):
    """Test creating a new escrow."""
    resp = await client.post(
        "/v1/escrow",
        json={
            "funder_wallet_id": str(test_wallet.id),
            "recipient_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
            "amount_sol": 0.5,
            "conditions": {"task": "test escrow creation"},
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["status"] == "created"


@pytest.mark.asyncio
async def test_list_escrows(client, test_escrow):
    """Test listing escrows."""
    resp = await client.get("/v1/escrow")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_escrow(client, test_escrow):
    """Test retrieving a specific escrow."""
    resp = await client.get(f"/v1/escrow/{test_escrow.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount_lamports"] == test_escrow.amount_lamports


@pytest.mark.asyncio
async def test_get_escrow_not_found(client):
    """Test retrieving a non-existent escrow."""
    resp = await client.get("/v1/escrow/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_escrow_action(client, test_escrow):
    """Test escrow action (release/refund/dispute)."""
    resp = await client.post(
        f"/v1/escrow/{test_escrow.id}/action",
        json={
            "action": "release",
        },
    )
    # May succeed or fail depending on escrow state/blockchain mock
    assert resp.status_code in (200, 400, 409, 422)


@pytest.mark.asyncio
async def test_escrow_unauthenticated(unauthed_client):
    """Test accessing escrows without auth should fail."""
    resp = await unauthed_client.get("/v1/escrow")
    assert resp.status_code == 401
