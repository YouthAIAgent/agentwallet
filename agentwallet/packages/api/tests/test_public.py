"""Tests for public (unauthenticated) endpoints."""

import uuid
from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_public_stats(unauthed_client):
    """Public stats endpoint returns 200 without auth."""
    resp = await unauthed_client.get("/v1/public/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_agents" in data
    assert "total_wallets" in data
    assert "total_transactions" in data
    assert "total_escrows" in data
    assert "total_acp_jobs" in data
    assert "total_swarms" in data
    assert "total_volume_sol" in data
    assert "api_endpoints" in data
    assert "mcp_tools" in data
    assert "tests_passing" in data
    assert "router_groups" in data
    assert isinstance(data["total_agents"], int)
    assert isinstance(data["total_volume_sol"], float)
    assert data["api_endpoints"] == 88
    assert data["mcp_tools"] == 27


@pytest.mark.asyncio
async def test_public_feed(unauthed_client):
    """Public feed endpoint returns 200 without auth."""
    resp = await unauthed_client.get("/v1/public/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "generated_at" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_public_feed_with_data(unauthed_client, db_session, test_org, test_wallet):
    """Public feed returns items when transactions exist."""
    from agentwallet.models import Transaction

    tx = Transaction(
        org_id=test_org.id,
        wallet_id=test_wallet.id,
        tx_type="transfer_sol",
        status="confirmed",
        from_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        to_address="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        amount_lamports=250_000_000,
    )
    db_session.add(tx)
    await db_session.commit()

    resp = await unauthed_client.get("/v1/public/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    item = data["items"][0]
    assert item["type"] == "transfer"
    assert item["action"] == "transferred"
    assert "address" in item
    assert "SOL" in item["amount"]
    # Verify address is truncated (anonymized)
    assert "..." in item["address"]


@pytest.mark.asyncio
async def test_public_stats_counts(unauthed_client, db_session, test_org, test_agent, test_wallet):
    """Public stats reflect actual DB counts."""
    resp = await unauthed_client.get("/v1/public/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_agents"] >= 1
    assert data["total_wallets"] >= 1
