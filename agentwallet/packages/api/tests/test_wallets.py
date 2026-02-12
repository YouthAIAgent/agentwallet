"""Tests for wallet operations."""

import pytest


@pytest.mark.asyncio
async def test_create_wallet(client):
    """Test creating a new wallet."""
    resp = await client.post("/v1/wallets", json={
        "wallet_type": "treasury",
        "label": "Test Treasury",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["wallet_type"] == "treasury"
    assert "address" in data
    assert len(data["address"]) > 30
    # Private key should never be exposed
    assert "encrypted_key" not in data


@pytest.mark.asyncio
async def test_list_wallets(client, test_wallet):
    """Test listing wallets."""
    resp = await client.get("/v1/wallets")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_wallet(client, test_wallet):
    """Test retrieving a specific wallet."""
    resp = await client.get(f"/v1/wallets/{test_wallet.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["address"] == test_wallet.address


@pytest.mark.asyncio
async def test_get_wallet_not_found(client):
    """Test retrieving a non-existent wallet."""
    resp = await client.get("/v1/wallets/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_wallet_balance(client, test_wallet, mock_solana_rpc):
    """Test getting wallet balance."""
    resp = await client.get(f"/v1/wallets/{test_wallet.id}/balance")
    assert resp.status_code == 200
    data = resp.json()
    assert "sol_balance" in data or "balance" in data


@pytest.mark.asyncio
async def test_wallets_unauthenticated(unauthed_client):
    """Test accessing wallets without auth should fail."""
    resp = await unauthed_client.get("/v1/wallets")
    assert resp.status_code == 401
