"""Security audit tests -- replay protection, auth validation, permissions."""

import base64
import json
import time
from unittest.mock import AsyncMock, patch

import pytest
from agentwallet.services.x402_server import get_pricing_config


@pytest.fixture(autouse=True)
def reset_x402_config():
    """Reset the global x402 pricing config + verification cache."""
    config = get_pricing_config()
    config.enabled = False
    config._routes = []
    config._payments = {}
    config._verified_signatures = {}
    yield
    config.enabled = False
    config._routes = []
    config._payments = {}
    config._verified_signatures = {}


def _proof(signature: str, amount: str = "100000", timestamp: int | None = None) -> str:
    payload = {"signature": signature, "amount": amount}
    if timestamp is not None:
        payload["timestamp"] = timestamp
    return base64.b64encode(json.dumps({"payload": payload}).encode()).decode()


def _enable_paywall(price_lamports: int = 100_000, pay_to: str = "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3"):
    config = get_pricing_config()
    config.configure(
        pricing=[
            {
                "route_pattern": "/agents/*",
                "method": "GET",
                "price_lamports": price_lamports,
                "description": "Pay to view agents",
                "pay_to": pay_to,
            }
        ],
        enabled=True,
        network="solana-mainnet",
    )


# ── x402 replay protection ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_replay_proof_expires_after_deadline(client, test_agent):
    """A proof that was cached as valid must NOT pass after max_deadline."""
    _enable_paywall()
    sig = "5" * 87

    with (
        patch(
            "agentwallet.services.x402_server.confirm_transaction",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "agentwallet.services.x402_server.verify_transfer_on_chain",
            new=AsyncMock(
                return_value={
                    "valid": True,
                    "payer": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "payee": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                    "amount": 100_000,
                    "token_mint": None,
                    "error": None,
                }
            ),
        ),
    ):
        proof = _proof(sig, timestamp=int(time.time()))
        # First request: verifies on-chain and caches
        resp = await client.get(f"/v1/agents/{test_agent.id}", headers={"X-PAYMENT": proof})
        assert resp.status_code == 200

        # Backdate the cache entry beyond max_deadline (60s)
        config = get_pricing_config()
        entry = config._verified_signatures[sig]
        entry["verified_at"] = time.time() - 3600

        # Replay: must be rejected even though it's cached
        resp2 = await client.get(f"/v1/agents/{test_agent.id}", headers={"X-PAYMENT": proof})
        assert resp2.status_code == 402
        assert "expired" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_replay_proof_rejected_for_different_payee(client, test_agent):
    """A cached proof must not be reusable for a route with a different payee."""
    _enable_paywall(pay_to="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3")
    sig = "5" * 87

    with (
        patch(
            "agentwallet.services.x402_server.confirm_transaction",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "agentwallet.services.x402_server.verify_transfer_on_chain",
            new=AsyncMock(
                return_value={
                    "valid": True,
                    "payer": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "payee": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                    "amount": 100_000,
                    "token_mint": None,
                    "error": None,
                }
            ),
        ),
    ):
        proof = _proof(sig, timestamp=int(time.time()))
        resp = await client.get(f"/v1/agents/{test_agent.id}", headers={"X-PAYMENT": proof})
        assert resp.status_code == 200

        # Reconfigure to a different payee and retry the same proof
        _enable_paywall(pay_to="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
        resp2 = await client.get(f"/v1/agents/{test_agent.id}", headers={"X-PAYMENT": proof})
        assert resp2.status_code == 402
        assert "payee" in resp2.json()["detail"]


# ── API key permissions ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_key_without_wallet_permission_cannot_transfer(
    client, test_org, db_session
):
    """An API key with no 'wallets' permission must be denied transfers."""
    from agentwallet.api.middleware.auth import hash_api_key
    from agentwallet.models.api_key import ApiKey

    raw_key = f"aw_live_{'x' * 40}"
    api_key = ApiKey(
        org_id=test_org.id,
        key_hash=hash_api_key(raw_key),
        key_prefix="aw_live_xxx...",
        name="read-only",
        permissions={"agents": "r"},
    )
    db_session.add(api_key)
    await db_session.commit()

    headers = {"X-API-Key": raw_key}
    resp = await client.post(
        "/v1/transactions/transfer-sol",
        headers=headers,
        json={
            "from_wallet_id": "00000000-0000-0000-0000-000000000000",
            "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
            "amount_sol": 0.1,
        },
    )
    assert resp.status_code == 403
    assert "wallets" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_api_key_with_wallet_permission_passes_permission_gate(
    client, test_org, db_session
):
    """A key with 'wallets: w' passes the permission gate (fails later on missing wallet)."""
    from agentwallet.api.middleware.auth import hash_api_key
    from agentwallet.models.api_key import ApiKey

    raw_key = f"aw_live_{'y' * 40}"
    api_key = ApiKey(
        org_id=test_org.id,
        key_hash=hash_api_key(raw_key),
        key_prefix="aw_live_yyy...",
        name="wallet-writer",
        permissions={"wallets": "rw", "agents": "r"},
    )
    db_session.add(api_key)
    await db_session.commit()

    resp = await client.post(
        "/v1/transactions/transfer-sol",
        headers={"X-API-Key": raw_key},
        json={
            "from_wallet_id": "00000000-0000-0000-0000-000000000000",
            "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
            "amount_sol": 0.1,
        },
    )
    # Passes permission gate (no 403); fails with 404 for unknown wallet
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_key_without_x402_permission_cannot_configure(client, test_org, db_session):
    """A key lacking 'x402' permission must be denied configuring pricing."""
    from agentwallet.api.middleware.auth import hash_api_key
    from agentwallet.models.api_key import ApiKey

    raw_key = f"aw_live_{'z' * 40}"
    api_key = ApiKey(
        org_id=test_org.id,
        key_hash=hash_api_key(raw_key),
        key_prefix="aw_live_zzz...",
        name="no-x402",
        permissions={"agents": "r"},
    )
    db_session.add(api_key)
    await db_session.commit()

    resp = await client.post(
        "/v1/x402/configure",
        headers={"X-API-Key": raw_key},
        json={
            "pricing": [
                {
                    "route_pattern": "/agents/*",
                    "method": "GET",
                    "price_lamports": 100_000,
                    "pay_to": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                }
            ],
            "enabled": True,
        },
    )
    assert resp.status_code == 403


# ── JWT user validation ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_disabled_user_token_rejected(client, test_user, test_org, db_session):
    """A JWT for a disabled user must be rejected."""
    from agentwallet.api.middleware.auth import create_access_token

    test_user.is_active = False
    await db_session.commit()

    token = create_access_token(test_user.id, test_org.id)
    resp = await client.get("/v1/agents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_user_org_mismatch_token_rejected(client, test_org, db_session):
    """A token whose user belongs to a different org must be rejected."""
    from agentwallet.api.middleware.auth import create_access_token, hash_password
    from agentwallet.models.organization import Organization
    from agentwallet.models.user import User

    other_org = Organization(name="Other Org", email="other@example.com", is_active=True)
    db_session.add(other_org)
    await db_session.flush()

    user = User(
        org_id=other_org.id,
        email="other-user@example.com",
        password_hash=hash_password("TestPassword123!"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Token claims test_org.id but user belongs to other_org
    token = create_access_token(user.id, test_org.id)
    resp = await client.get("/v1/agents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
