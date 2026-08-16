"""Tests for the human-facing task marketplace endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.fixture
async def org_wallet(db_session, test_org):
    """An org-level (non-agent) wallet so tasks have a funder."""
    from agentwallet.models import Wallet

    wallet = Wallet(
        org_id=test_org.id,
        agent_id=None,
        address=f"Org{uuid.uuid4().hex[:28]}Addr",
        wallet_type="treasury",
        encrypted_key="encrypted_test_key_placeholder",
        label="Org Treasury",
        is_active=True,
    )
    db_session.add(wallet)
    await db_session.commit()
    await db_session.refresh(wallet)
    return wallet


@pytest.fixture
def mock_escrow_fund():
    """Mock the on-chain escrow funding + release/refund calls."""
    from solders.keypair import Keypair

    sig = "mocktx" + "a" * 60
    kp = Keypair()
    with (
        patch(
            "agentwallet.services.escrow_service.transfer_sol",
            new=AsyncMock(return_value=sig),
        ),
        patch(
            "agentwallet.services.escrow_service.confirm_transaction",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "agentwallet.services.escrow_service.load_platform_keypair",
            new=AsyncMock(return_value=kp),
        ),
        patch(
            "agentwallet.services.wallet_manager.WalletManager._decrypt_keypair",
            new=MagicMock(return_value=kp),
        ),
    ):
        yield sig


@pytest.fixture
def task_payload(created_agent):
    return {
        "title": "Research AI agent market",
        "description": "Write a concise market research summary on the AI agent economy.",
        "price_usdc": 5.0,
        "category": "research",
        "capability": "analysis",
        "auto_assign": False,
    }


@pytest.mark.asyncio
async def test_post_task(client: AsyncClient, task_payload, org_wallet, mock_escrow_fund):
    resp = await client.post("/v1/marketplace/tasks", json=task_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Research AI agent market"
    assert data["price_usdc"] == 5.0
    assert data["status"] in ("posted", "funded")
    assert data["escrow_id"] is not None
    assert data["platform_fee_usdc"] > 0


@pytest.mark.asyncio
async def test_post_task_auto_assign(
    client: AsyncClient, created_agent, test_wallet, task_payload, org_wallet, mock_escrow_fund
):
    task_payload["auto_assign"] = True
    resp = await client.post("/v1/marketplace/tasks", json=task_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_id"] == created_agent["id"]
    assert data["agent_name"] == "Test Agent"
    assert data["status"] in ("assigned", "funded")


@pytest.fixture
async def public_specialist(db_session, test_org):
    """A public specialist from another org (marketplace roster)."""
    from agentwallet.models import Agent, Organization, Wallet

    org = Organization(name="Specialists Org", email=f"spec{uuid.uuid4().hex[:10]}@test.dev")
    db_session.add(org)
    await db_session.flush()

    agent = Agent(
        org_id=org.id,
        name="Security Architect",
        description="Threat modeling specialist",
        capabilities=["security", "audit", "threat-modeling"],
        is_public=True,
        status="active",
    )
    db_session.add(agent)
    await db_session.flush()

    wallet = Wallet(
        org_id=org.id,
        agent_id=agent.id,
        address=f"Pub{uuid.uuid4().hex[:28]}Addr",
        wallet_type="agent",
        encrypted_key="encrypted_test_key_placeholder",
        label="Specialist Wallet",
        is_active=True,
    )
    db_session.add(wallet)
    await db_session.flush()
    agent.default_wallet_id = wallet.id
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.mark.asyncio
async def test_auto_assign_falls_back_to_public_specialist(
    client: AsyncClient, public_specialist, task_payload, org_wallet, mock_escrow_fund
):
    """With no matching org agent, a public specialist is auto-assigned."""
    task_payload["capability"] = "security"
    task_payload["auto_assign"] = True
    resp = await client.post("/v1/marketplace/tasks", json=task_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_id"] == str(public_specialist.id)
    assert data["agent_name"] == "Security Architect"
    assert data["status"] in ("assigned", "funded")


@pytest.mark.asyncio
async def test_manual_assign_public_specialist(
    client: AsyncClient, public_specialist, task_payload, org_wallet, mock_escrow_fund
):
    """A task can be manually assigned to a public specialist directly."""
    created = await client.post("/v1/marketplace/tasks", json=task_payload)
    task_id = created.json()["id"]
    resp = await client.post(
        f"/v1/marketplace/tasks/{task_id}/assign",
        json={"agent_id": str(public_specialist.id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == str(public_specialist.id)
    assert data["agent_name"] == "Security Architect"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, task_payload, org_wallet, mock_escrow_fund):
    await client.post("/v1/marketplace/tasks", json=task_payload)
    resp = await client.get("/v1/marketplace/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_task_stats(client: AsyncClient, task_payload, org_wallet, mock_escrow_fund):
    await client.post("/v1/marketplace/tasks", json=task_payload)
    resp = await client.get("/v1/marketplace/tasks/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tasks"] >= 1
    assert "platform_fees_usdc" in data


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, task_payload, org_wallet, mock_escrow_fund):
    created = await client.post("/v1/marketplace/tasks", json=task_payload)
    task_id = created.json()["id"]
    resp = await client.get(f"/v1/marketplace/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_run_and_deliver(client: AsyncClient, task_payload, org_wallet, mock_escrow_fund):
    """Post → run → deliver should release the escrow (mocked on-chain)."""
    created = await client.post("/v1/marketplace/tasks", json=task_payload)
    task_id = created.json()["id"]

    run_resp = await client.post(f"/v1/marketplace/tasks/{task_id}/run")
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == "in_progress"

    deliver_resp = await client.post(
        f"/v1/marketplace/tasks/{task_id}/deliver",
        json={"result_data": {"output": "delivered work"}, "delivery_notes": "done", "auto_release": True},
    )
    assert deliver_resp.status_code == 200
    data = deliver_resp.json()
    assert data["status"] == "released"
    assert data["result_data"]["output"] == "delivered work"
    assert data["delivered_at"] is not None
    assert data["released_at"] is not None


@pytest.mark.asyncio
async def test_refund_task(client: AsyncClient, task_payload, org_wallet, mock_escrow_fund):
    created = await client.post("/v1/marketplace/tasks", json=task_payload)
    task_id = created.json()["id"]
    resp = await client.post(
        f"/v1/marketplace/tasks/{task_id}/refund",
        json={"reason": "changed my mind"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "refunded"


@pytest.mark.asyncio
async def test_cancel_task(client: AsyncClient, task_payload, org_wallet, mock_escrow_fund):
    created = await client.post("/v1/marketplace/tasks", json=task_payload)
    task_id = created.json()["id"]
    resp = await client.post(f"/v1/marketplace/tasks/{task_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_invalid_price_rejected(client: AsyncClient, org_wallet, mock_escrow_fund):
    payload = {
        "title": "Cheap task",
        "description": "This should be rejected.",
        "price_usdc": 0,
        "category": "general",
    }
    resp = await client.post("/v1/marketplace/tasks", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    resp = await client.get(f"/v1/marketplace/tasks/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_access():
    from agentwallet.main import app
    from httpx import ASGITransport
    from httpx import AsyncClient as AC

    transport = ASGITransport(app=app)
    async with AC(transport=transport, base_url="http://test") as unauthed:
        resp = await unauthed.get("/v1/marketplace/tasks")
        assert resp.status_code in (401, 403)
