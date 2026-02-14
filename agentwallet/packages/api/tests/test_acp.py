"""Tests for ACP (Agent Commerce Protocol) endpoints."""

import uuid

import pytest

from agentwallet.models import Agent


@pytest.fixture
async def seller_agent(db_session, test_org):
    agent = Agent(
        org_id=test_org.id,
        name="Seller Agent",
        description="A seller agent for testing",
        status="active",
        capabilities=["data-analysis"],
        is_public=True,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.fixture
async def acp_job(client, test_agent, seller_agent):
    """Create an ACP job and return the response data."""
    resp = await client.post(
        "/v1/acp/jobs",
        json={
            "buyer_agent_id": str(test_agent.id),
            "seller_agent_id": str(seller_agent.id),
            "title": "Market Analysis Report",
            "description": "Analyze top 10 DeFi tokens",
            "price_usdc": 5.0,
            "requirements": {"format": "pdf", "tokens": 10},
            "deliverables": {"report": True},
        },
    )
    assert resp.status_code == 200
    return resp.json()


# ── Job CRUD ──


@pytest.mark.asyncio
async def test_create_acp_job(client, test_agent, seller_agent):
    resp = await client.post(
        "/v1/acp/jobs",
        json={
            "buyer_agent_id": str(test_agent.id),
            "seller_agent_id": str(seller_agent.id),
            "title": "Test ACP Job",
            "description": "Test description",
            "price_usdc": 10.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "request"
    assert data["title"] == "Test ACP Job"
    assert data["agreed_price_lamports"] == 10_000_000


@pytest.mark.asyncio
async def test_list_acp_jobs(client, acp_job):
    resp = await client.get("/v1/acp/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["jobs"]) >= 1


@pytest.mark.asyncio
async def test_get_acp_job(client, acp_job):
    resp = await client.get(f"/v1/acp/jobs/{acp_job['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == acp_job["id"]


@pytest.mark.asyncio
async def test_get_acp_job_not_found(client):
    resp = await client.get(f"/v1/acp/jobs/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── 4-Phase Lifecycle ──


@pytest.mark.asyncio
async def test_acp_full_lifecycle(client, test_agent, seller_agent):
    # Phase 1: Create job (request)
    resp = await client.post(
        "/v1/acp/jobs",
        json={
            "buyer_agent_id": str(test_agent.id),
            "seller_agent_id": str(seller_agent.id),
            "title": "Full Lifecycle Job",
            "description": "Testing all 4 phases",
            "price_usdc": 25.0,
        },
    )
    assert resp.status_code == 200
    job = resp.json()
    assert job["phase"] == "request"
    job_id = job["id"]

    # Phase 2: Negotiate
    resp = await client.post(
        f"/v1/acp/jobs/{job_id}/negotiate",
        params={"seller_agent_id": str(seller_agent.id)},
        json={
            "agreed_terms": {"deadline": "24h", "format": "json"},
            "agreed_price_usdc": 20.0,
        },
    )
    assert resp.status_code == 200
    job = resp.json()
    assert job["phase"] == "negotiation"
    assert job["negotiated_at"] is not None

    # Phase 3: Fund (buyer funds escrow)
    resp = await client.post(
        f"/v1/acp/jobs/{job_id}/fund",
        params={"buyer_agent_id": str(test_agent.id)},
    )
    assert resp.status_code == 200
    job = resp.json()
    assert job["phase"] == "transaction"
    assert job["transacted_at"] is not None

    # Phase 4a: Deliver
    resp = await client.post(
        f"/v1/acp/jobs/{job_id}/deliver",
        params={"seller_agent_id": str(seller_agent.id)},
        json={
            "result_data": {"analysis": "BTC up 20%", "confidence": 0.95},
            "notes": "Completed ahead of schedule",
        },
    )
    assert resp.status_code == 200
    job = resp.json()
    assert job["phase"] == "evaluation"

    # Phase 4b: Evaluate (buyer approves)
    resp = await client.post(
        f"/v1/acp/jobs/{job_id}/evaluate",
        params={"evaluator_agent_id": str(test_agent.id)},
        json={
            "approved": True,
            "evaluation_notes": "Excellent work",
            "rating": 5,
        },
    )
    assert resp.status_code == 200
    job = resp.json()
    assert job["phase"] == "completed"
    assert job["evaluation_approved"] is True
    assert job["rating"] == 5
    assert job["completed_at"] is not None


# ── Memos ──


@pytest.mark.asyncio
async def test_send_memo(client, acp_job, test_agent):
    resp = await client.post(
        f"/v1/acp/jobs/{acp_job['id']}/memos",
        params={"sender_agent_id": str(test_agent.id)},
        json={
            "memo_type": "general",
            "content": {"message": "Hello from buyer"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["memo_type"] == "general"
    assert data["advances_phase"] is False


@pytest.mark.asyncio
async def test_list_memos(client, acp_job):
    resp = await client.get(f"/v1/acp/jobs/{acp_job['id']}/memos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1  # At least the auto-created job_request memo


# ── Resource Offerings ──


@pytest.mark.asyncio
async def test_create_offering(client, test_agent):
    resp = await client.post(
        "/v1/acp/offerings",
        json={
            "agent_id": str(test_agent.id),
            "name": "Price Feed",
            "description": "Real-time token price data",
            "endpoint_path": "/v1/resources/price-feed/data",
            "parameters": {"token": "string", "interval": "string"},
            "response_schema": {"price": "float", "timestamp": "int"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Price Feed"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_offerings(client, test_agent):
    # Create one first
    await client.post(
        "/v1/acp/offerings",
        json={
            "agent_id": str(test_agent.id),
            "name": "Listing Test Offering",
            "description": "For list test",
            "endpoint_path": "/v1/resources/test/data",
        },
    )
    resp = await client.get("/v1/acp/offerings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


# ── Auth ──


@pytest.mark.asyncio
async def test_acp_unauthenticated(unauthed_client):
    resp = await unauthed_client.get("/v1/acp/jobs")
    assert resp.status_code == 401
