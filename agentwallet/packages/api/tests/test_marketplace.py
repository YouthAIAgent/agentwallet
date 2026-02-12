"""Tests for marketplace endpoints — services, jobs, reputation."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.fixture
def service_payload(created_agent):
    return {
        "agent_id": str(created_agent["id"]),
        "name": "Data Analysis Service",
        "description": "AI-powered data analysis and reporting",
        "price_usdc": 10.0,
        "capabilities": ["analysis", "reporting"],
        "estimated_duration_hours": 24,
        "max_concurrent_jobs": 3,
        "requirements": {"input_format": "csv"},
        "delivery_format": "json",
    }


# ── Service Endpoints ─────────────────────────────────────


@pytest.mark.asyncio
async def test_register_service(client: AsyncClient, service_payload):
    resp = await client.post("/v1/marketplace/services", json=service_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Data Analysis Service"
    assert data["price_usdc"] == 10.0
    assert data["capabilities"] == ["analysis", "reporting"]
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_service_duplicate(client: AsyncClient, service_payload):
    await client.post("/v1/marketplace/services", json=service_payload)
    resp = await client.post("/v1/marketplace/services", json=service_payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_discover_services(client: AsyncClient, service_payload):
    await client.post("/v1/marketplace/services", json=service_payload)
    resp = await client.get("/v1/marketplace/services")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_discover_services_by_capability(client: AsyncClient, service_payload):
    await client.post("/v1/marketplace/services", json=service_payload)
    resp = await client.get("/v1/marketplace/services", params={"capability": "analysis"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_service(client: AsyncClient, service_payload):
    create_resp = await client.post("/v1/marketplace/services", json=service_payload)
    service_id = create_resp.json()["id"]
    resp = await client.get(f"/v1/marketplace/services/{service_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == service_id


@pytest.mark.asyncio
async def test_get_service_not_found(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/v1/marketplace/services/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_service(client: AsyncClient, service_payload):
    create_resp = await client.post("/v1/marketplace/services", json=service_payload)
    service_id = create_resp.json()["id"]
    resp = await client.patch(
        f"/v1/marketplace/services/{service_id}",
        json={"name": "Updated Service", "price_usdc": 25.0},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Service"
    assert resp.json()["price_usdc"] == 25.0


@pytest.mark.asyncio
async def test_service_analytics(client: AsyncClient, service_payload):
    create_resp = await client.post("/v1/marketplace/services", json=service_payload)
    service_id = create_resp.json()["id"]
    resp = await client.get(f"/v1/marketplace/services/{service_id}/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_jobs" in data
    assert "success_rate" in data


# ── Reputation & Leaderboard ─────────────────────────────


@pytest.mark.asyncio
async def test_get_reputation(client: AsyncClient, created_agent):
    agent_id = created_agent["id"]
    resp = await client.get(f"/v1/marketplace/reputation/{agent_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == agent_id
    assert "score" in data
    assert "reliability_score" in data


@pytest.mark.asyncio
async def test_get_reputation_not_found(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/v1/marketplace/reputation/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_leaderboard(client: AsyncClient):
    resp = await client.get("/v1/marketplace/leaderboard", params={"min_jobs": 0})
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert "total_agents" in data


@pytest.mark.asyncio
async def test_marketplace_stats(client: AsyncClient):
    resp = await client.get("/v1/marketplace/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_services" in data
    assert "total_jobs" in data
    assert "total_volume_usdc" in data


# ── Auth ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthorized_access():
    from httpx import ASGITransport, AsyncClient as AC
    from agentwallet.main import app

    transport = ASGITransport(app=app)
    async with AC(transport=transport, base_url="http://test") as unauthed:
        resp = await unauthed.get("/v1/marketplace/services")
        assert resp.status_code in (401, 403)
