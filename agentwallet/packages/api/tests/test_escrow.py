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


@pytest.mark.asyncio
async def test_escrow_release_disburses_from_platform(
    client, db_session, test_escrow, monkeypatch
):
    """Release must disburse FROM the platform custody wallet, NOT the funder.

    Regression test for the double-pay bug where the funder was charged a
    second time at release (fund pays into custody, then release paid out of
    the funder's wallet again).
    """
    from agentwallet.services import escrow_service as svc
    from solders.keypair import Keypair

    test_escrow.status = "funded"
    await db_session.commit()

    platform_kp = Keypair()
    sent = {}

    async def fake_transfer(client, from_keypair, to_address, lamports, **kw):
        sent["from"] = str(from_keypair.pubkey())
        sent["to"] = to_address
        sent["lamports"] = lamports
        return "sig-release-1"

    async def fake_confirm(client_, sig):
        return True

    monkeypatch.setattr(svc, "load_platform_keypair", lambda: platform_kp)
    monkeypatch.setattr(svc, "transfer_sol", fake_transfer)
    monkeypatch.setattr(svc, "confirm_transaction", fake_confirm)

    resp = await client.post(
        f"/v1/escrow/{test_escrow.id}/action", json={"action": "release"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "released"
    assert data["release_signature"] == "sig-release-1"
    # Funds come from the custody wallet, to the recipient
    assert sent["from"] == str(platform_kp.pubkey())
    assert sent["to"] == test_escrow.recipient_address
    assert sent["lamports"] == test_escrow.amount_lamports


@pytest.mark.asyncio
async def test_escrow_refund_returns_to_funder(
    client, db_session, test_escrow, test_wallet, monkeypatch
):
    """Refund must return custody funds to the funder's wallet address."""
    from agentwallet.services import escrow_service as svc
    from solders.keypair import Keypair

    test_escrow.status = "funded"
    await db_session.commit()

    platform_kp = Keypair()
    sent = {}

    async def fake_transfer(client, from_keypair, to_address, lamports, **kw):
        sent["from"] = str(from_keypair.pubkey())
        sent["to"] = to_address
        sent["lamports"] = lamports
        return "sig-refund-1"

    async def fake_confirm(client_, sig):
        return True

    monkeypatch.setattr(svc, "load_platform_keypair", lambda: platform_kp)
    monkeypatch.setattr(svc, "transfer_sol", fake_transfer)
    monkeypatch.setattr(svc, "confirm_transaction", fake_confirm)

    resp = await client.post(
        f"/v1/escrow/{test_escrow.id}/action", json={"action": "refund"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "refunded"
    assert data["refund_signature"] == "sig-refund-1"
    # Custody -> funder's wallet address
    assert sent["from"] == str(platform_kp.pubkey())
    assert sent["to"] == test_wallet.address
    assert sent["lamports"] == test_escrow.amount_lamports


@pytest.mark.asyncio
async def test_escrow_release_requires_platform_key(
    client, db_session, test_escrow, monkeypatch
):
    """Release without a configured platform key must fail cleanly (409)."""
    from agentwallet.services import escrow_service as svc

    test_escrow.status = "funded"
    await db_session.commit()

    def boom():
        raise ValueError("Platform private key not configured")

    monkeypatch.setattr(svc, "load_platform_keypair", boom)

    resp = await client.post(
        f"/v1/escrow/{test_escrow.id}/action", json={"action": "release"}
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_escrow_dispute(client, db_session, test_escrow):
    """Dispute marks the escrow disputed with a reason (no on-chain move)."""
    test_escrow.status = "funded"
    await db_session.commit()

    resp = await client.post(
        f"/v1/escrow/{test_escrow.id}/action",
        json={"action": "dispute", "reason": "work not delivered"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "disputed"
    assert data["dispute_reason"] == "work not delivered"
