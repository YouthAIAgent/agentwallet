"""Tests for on-chain USDC subscription billing."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from agentwallet.core.database import get_session_factory
from agentwallet.core.exceptions import InsufficientBalanceError
from agentwallet.models import Organization


def _mock_transfer(signature: str | None = "mock-signature-123"):
    """Patch TokenService.transfer_token with a successful on-chain transfer."""
    tx = SimpleNamespace(id=uuid.uuid4(), signature=signature)
    return patch(
        "agentwallet.services.token_service.TokenService.transfer_token",
        new=AsyncMock(return_value=tx),
    )


async def _org_tier(org_id: uuid.UUID) -> str:
    """Read the org tier from the database in a fresh session."""
    factory = get_session_factory()
    async with factory() as session:
        org = await session.get(Organization, org_id)
        return org.tier


@pytest.mark.asyncio
async def test_billing_plans(client):
    """List plans with USDC pricing."""
    resp = await client.get("/v1/billing/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["plans"]) == 3
    by_tier = {p["tier"]: p for p in data["plans"]}
    assert by_tier["pro"]["price_usdc"] == 49.0
    assert by_tier["enterprise"]["price_usdc"] == 299.0
    assert by_tier["free"]["price_usdc"] == 0.0


@pytest.mark.asyncio
async def test_subscribe_pro(client, test_org, test_wallet):
    """Subscribe to pro — charges USDC on-chain and upgrades the org."""
    with _mock_transfer() as transfer:
        resp = await client.post(
            "/v1/billing/subscribe",
            json={"tier": "pro", "from_wallet_id": str(test_wallet.id)},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["subscription"]["tier"] == "pro"
    assert data["subscription"]["status"] == "active"
    assert data["subscription"]["amount_usdc"] == 49.0
    assert data["subscription"]["payment_signature"] == "mock-signature-123"

    # Payment went through the org's own token transfer infra, in USDC,
    # to the platform wallet.
    transfer.assert_awaited_once()
    kwargs = transfer.await_args.kwargs
    assert kwargs["token_symbol"] == "USDC"
    assert kwargs["amount"] == 49.0
    assert kwargs["to_address"] == "11111111111111111111111111111111"  # PLATFORM_WALLET_ADDRESS in tests

    # Org tier upgraded immediately.
    assert await _org_tier(test_org.id) == "pro"


@pytest.mark.asyncio
async def test_subscribe_enterprise(client, test_org, test_wallet):
    """Enterprise subscription charges 299 USDC."""
    with _mock_transfer():
        resp = await client.post(
            "/v1/billing/subscribe",
            json={"tier": "enterprise", "from_wallet_id": str(test_wallet.id)},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["subscription"]["tier"] == "enterprise"
    assert data["subscription"]["amount_usdc"] == 299.0
    assert await _org_tier(test_org.id) == "enterprise"


@pytest.mark.asyncio
async def test_subscribe_invalid_tier(client, test_wallet):
    """Unknown tier is rejected before any charge."""
    resp = await client.post(
        "/v1/billing/subscribe",
        json={"tier": "platinum", "from_wallet_id": str(test_wallet.id)},
    )
    assert resp.status_code == 400
    assert "Unknown tier" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_subscribe_insufficient_balance(client, test_org, test_wallet):
    """Insufficient USDC in the wallet is surfaced as a 400."""
    def _fail(*args, **kwargs):
        raise InsufficientBalanceError(available=0, required=49_000_000)

    with patch(
        "agentwallet.services.token_service.TokenService.transfer_token",
        new=AsyncMock(side_effect=_fail),
    ):
        resp = await client.post(
            "/v1/billing/subscribe",
            json={"tier": "pro", "from_wallet_id": str(test_wallet.id)},
        )

    assert resp.status_code == 400
    assert "balance" in resp.json()["detail"].lower()
    # Tier unchanged on failure.
    assert await _org_tier(test_org.id) == "pro"


@pytest.mark.asyncio
async def test_downgrade_to_free(client, test_org, test_wallet):
    """Subscribing to free cancels the paid subscription and downgrades."""
    with _mock_transfer():
        await client.post(
            "/v1/billing/subscribe",
            json={"tier": "pro", "from_wallet_id": str(test_wallet.id)},
        )

    # Downgrade — no payment involved.
    resp = await client.post(
        "/v1/billing/subscribe",
        json={"tier": "free", "from_wallet_id": str(test_wallet.id)},
    )
    assert resp.status_code == 201
    assert resp.json()["subscription"]["org_tier"] == "free"
    assert await _org_tier(test_org.id) == "free"


@pytest.mark.asyncio
async def test_get_subscription_state(client, test_org, test_wallet):
    """GET /v1/billing/subscription returns current state."""
    with _mock_transfer():
        await client.post(
            "/v1/billing/subscribe",
            json={"tier": "pro", "from_wallet_id": str(test_wallet.id)},
        )

    resp = await client.get("/v1/billing/subscription")
    assert resp.status_code == 200
    data = resp.json()["subscription"]
    assert data["tier"] == "pro"
    assert data["status"] == "active"
    assert data["period_start"] is not None
    assert data["period_end"] is not None


@pytest.mark.asyncio
async def test_get_subscription_no_subscription(client, test_org):
    """Free org with no subscription history returns a clean state."""
    resp = await client.get("/v1/billing/subscription")
    assert resp.status_code == 200
    data = resp.json()["subscription"]
    assert data["status"] == "none"
    assert data["org_tier"] == test_org.tier


@pytest.mark.asyncio
async def test_renew(client, test_org, test_wallet):
    """Renew extends the period and charges again."""
    with _mock_transfer("sig-1") as transfer:
        await client.post(
            "/v1/billing/subscribe",
            json={"tier": "pro", "from_wallet_id": str(test_wallet.id)},
        )

    with _mock_transfer("sig-2"):
        resp = await client.post(
            "/v1/billing/renew",
            json={"from_wallet_id": str(test_wallet.id)},
        )

    assert resp.status_code == 200
    data = resp.json()["subscription"]
    assert data["status"] == "active"
    assert data["payment_signature"] == "sig-2"
    assert transfer.await_count == 1  # subscribe charged once, renew charged once more


@pytest.mark.asyncio
async def test_renew_without_subscription(client, test_org, test_wallet):
    """Renewing with no active subscription is rejected."""
    resp = await client.post(
        "/v1/billing/renew",
        json={"from_wallet_id": str(test_wallet.id)},
    )
    assert resp.status_code == 400
    assert "No active subscription" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_cancel(client, test_org, test_wallet):
    """Cancel downgrades the org to free immediately."""
    with _mock_transfer():
        await client.post(
            "/v1/billing/subscribe",
            json={"tier": "pro", "from_wallet_id": str(test_wallet.id)},
        )

    resp = await client.post("/v1/billing/cancel")
    assert resp.status_code == 200
    data = resp.json()["subscription"]
    assert data["status"] == "cancelled"
    assert data["org_tier"] == "free"
    assert await _org_tier(test_org.id) == "free"


@pytest.mark.asyncio
async def test_cancel_without_subscription(client, test_org):
    """Cancelling with no active subscription is rejected."""
    resp = await client.post("/v1/billing/cancel")
    assert resp.status_code == 400
    assert "No active subscription" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_billing_unauthenticated(unauthed_client):
    """Billing endpoints require auth."""
    resp = await unauthed_client.get("/v1/billing/plans")
    assert resp.status_code == 401
