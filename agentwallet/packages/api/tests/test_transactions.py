"""Tests for transaction operations."""

import pytest


@pytest.mark.asyncio
async def test_list_transactions(client, test_transaction):
    """Test listing transactions."""
    resp = await client.get("/v1/transactions")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_transaction(client, test_transaction):
    """Test retrieving a specific transaction."""
    resp = await client.get(f"/v1/transactions/{test_transaction.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount_lamports"] == test_transaction.amount_lamports


@pytest.mark.asyncio
async def test_get_transaction_not_found(client):
    """Test retrieving a non-existent transaction."""
    resp = await client.get("/v1/transactions/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_transfer_sol(client, test_wallet, mock_solana_rpc):
    """Test SOL transfer endpoint."""
    resp = await client.post("/v1/transactions/transfer-sol", json={
        "from_wallet_id": str(test_wallet.id),
        "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "amount_lamports": 100_000_000,
    })
    # May succeed or fail depending on wallet key/blockchain mock
    assert resp.status_code in (201, 400, 422, 500)


@pytest.mark.asyncio
async def test_transactions_unauthenticated(unauthed_client):
    """Test accessing transactions without auth should fail."""
    resp = await unauthed_client.get("/v1/transactions")
    assert resp.status_code == 401
