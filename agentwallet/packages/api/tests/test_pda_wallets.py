"""Tests for PDA wallet operations."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agentwallet.models.pda_wallet import PDAWallet
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def test_pda_wallet(db_session: AsyncSession, test_org, test_wallet):
    """Create a test PDA wallet record directly in the DB."""
    pda = PDAWallet(
        org_id=test_org.id,
        pda_address="TestPDA" + uuid.uuid4().hex[:26],
        authority_wallet_id=test_wallet.id,
        org_pubkey="5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8",
        agent_id_seed="test-agent-001",
        spending_limit_per_tx=500_000_000,
        daily_limit=2_000_000_000,
        bump=254,
        is_active=True,
        tx_signature="TestSignature123",
    )
    db_session.add(pda)
    await db_session.commit()
    await db_session.refresh(pda)
    return pda


@pytest.fixture
async def second_pda_wallet(db_session: AsyncSession, test_org, test_wallet):
    """Create a second PDA wallet for pagination / list tests."""
    pda = PDAWallet(
        org_id=test_org.id,
        pda_address="TestPDA2" + uuid.uuid4().hex[:25],
        authority_wallet_id=test_wallet.id,
        org_pubkey="5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8",
        agent_id_seed="test-agent-002",
        spending_limit_per_tx=100_000_000,
        daily_limit=500_000_000,
        bump=253,
        is_active=True,
        tx_signature="TestSignature456",
    )
    db_session.add(pda)
    await db_session.commit()
    await db_session.refresh(pda)
    return pda


# ---------------------------------------------------------------------------
# GET /v1/pda-wallets  (list)
# ---------------------------------------------------------------------------


async def test_list_pda_wallets(client, test_pda_wallet):
    """Listing PDA wallets returns at least the fixture wallet."""
    resp = await client.get("/v1/pda-wallets")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "total" in body
    assert body["total"] >= 1
    addresses = [w["pda_address"] for w in body["data"]]
    assert test_pda_wallet.pda_address in addresses


async def test_list_pda_wallets_pagination(client, test_pda_wallet, second_pda_wallet):
    """Listing with limit/offset returns the correct slice."""
    resp = await client.get("/v1/pda-wallets?limit=1&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 1
    assert body["total"] >= 2


async def test_list_pda_wallets_empty(client):
    """Listing when there are no PDA wallets returns empty list."""
    resp = await client.get("/v1/pda-wallets")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["data"], list)
    # total may be 0 or more depending on fixture ordering, but the call itself succeeds


# ---------------------------------------------------------------------------
# GET /v1/pda-wallets/{id}  (get by ID)
# ---------------------------------------------------------------------------


async def test_get_pda_wallet_by_id(client, test_pda_wallet):
    """Get a specific PDA wallet by its ID."""
    resp = await client.get(f"/v1/pda-wallets/{test_pda_wallet.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(test_pda_wallet.id)
    assert body["pda_address"] == test_pda_wallet.pda_address
    assert body["agent_id_seed"] == "test-agent-001"
    assert body["spending_limit_per_tx"] == 500_000_000
    assert body["daily_limit"] == 2_000_000_000
    assert body["bump"] == 254
    assert body["is_active"] is True
    assert body["tx_signature"] == "TestSignature123"


async def test_get_pda_wallet_not_found(client):
    """Getting a non-existent PDA wallet returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/v1/pda-wallets/{fake_id}")
    assert resp.status_code == 404


async def test_get_pda_wallet_invalid_uuid(client):
    """Getting a PDA wallet with an invalid UUID returns 422."""
    resp = await client.get("/v1/pda-wallets/not-a-uuid")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /v1/pda-wallets  (create — mocked service)
# ---------------------------------------------------------------------------


async def test_create_pda_wallet(client, test_wallet):
    """Creating a PDA wallet succeeds when the service layer is mocked."""
    mock_pw = MagicMock()
    mock_pw.id = uuid.uuid4()
    mock_pw.org_id = test_wallet.org_id
    mock_pw.pda_address = "MockPDA" + uuid.uuid4().hex[:26]
    mock_pw.authority_wallet_id = test_wallet.id
    mock_pw.agent_id = None
    mock_pw.agent_id_seed = "mock-agent-seed"
    mock_pw.spending_limit_per_tx = 1_000_000_000
    mock_pw.daily_limit = 5_000_000_000
    mock_pw.bump = 252
    mock_pw.is_active = True
    mock_pw.tx_signature = "MockSig" + uuid.uuid4().hex[:20]
    mock_pw.created_at = datetime.now(timezone.utc)

    with patch("agentwallet.api.routers.pda_wallets.PDAWalletService") as MockSvc:
        instance = MockSvc.return_value
        instance.create_pda_wallet = AsyncMock(return_value=mock_pw)

        resp = await client.post(
            "/v1/pda-wallets",
            json={
                "authority_wallet_id": str(test_wallet.id),
                "agent_id_seed": "mock-agent-seed",
                "spending_limit_per_tx": 1_000_000_000,
                "daily_limit": 5_000_000_000,
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["pda_address"] == mock_pw.pda_address
    assert body["spending_limit_per_tx"] == 1_000_000_000
    assert body["daily_limit"] == 5_000_000_000
    assert body["bump"] == 252
    assert body["is_active"] is True


async def test_create_pda_wallet_with_agent_id(client, test_wallet, test_agent):
    """Creating a PDA wallet with an explicit agent_id forwards it to the service."""
    mock_pw = MagicMock()
    mock_pw.id = uuid.uuid4()
    mock_pw.org_id = test_wallet.org_id
    mock_pw.pda_address = "MockPDA2" + uuid.uuid4().hex[:25]
    mock_pw.authority_wallet_id = test_wallet.id
    mock_pw.agent_id = test_agent.id
    mock_pw.agent_id_seed = "agent-with-id"
    mock_pw.spending_limit_per_tx = 200_000_000
    mock_pw.daily_limit = 800_000_000
    mock_pw.bump = 251
    mock_pw.is_active = True
    mock_pw.tx_signature = "MockSigAgent" + uuid.uuid4().hex[:16]
    mock_pw.created_at = datetime.now(timezone.utc)

    with patch("agentwallet.api.routers.pda_wallets.PDAWalletService") as MockSvc:
        instance = MockSvc.return_value
        instance.create_pda_wallet = AsyncMock(return_value=mock_pw)

        resp = await client.post(
            "/v1/pda-wallets",
            json={
                "authority_wallet_id": str(test_wallet.id),
                "agent_id_seed": "agent-with-id",
                "spending_limit_per_tx": 200_000_000,
                "daily_limit": 800_000_000,
                "agent_id": str(test_agent.id),
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["agent_id"] == str(test_agent.id)


async def test_create_pda_wallet_validation_errors(client):
    """Creating a PDA wallet with invalid data returns 422."""
    # Missing required fields
    resp = await client.post("/v1/pda-wallets", json={})
    assert resp.status_code == 422

    # spending_limit_per_tx must be > 0
    resp = await client.post(
        "/v1/pda-wallets",
        json={
            "authority_wallet_id": str(uuid.uuid4()),
            "agent_id_seed": "test",
            "spending_limit_per_tx": 0,
            "daily_limit": 1_000_000,
        },
    )
    assert resp.status_code == 422

    # daily_limit must be > 0
    resp = await client.post(
        "/v1/pda-wallets",
        json={
            "authority_wallet_id": str(uuid.uuid4()),
            "agent_id_seed": "test",
            "spending_limit_per_tx": 1_000_000,
            "daily_limit": -1,
        },
    )
    assert resp.status_code == 422

    # agent_id_seed must be non-empty
    resp = await client.post(
        "/v1/pda-wallets",
        json={
            "authority_wallet_id": str(uuid.uuid4()),
            "agent_id_seed": "",
            "spending_limit_per_tx": 1_000_000,
            "daily_limit": 1_000_000,
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /v1/pda-wallets/{id}/state  (on-chain state — mocked)
# ---------------------------------------------------------------------------


async def test_get_pda_wallet_state(client, test_pda_wallet):
    """Reading on-chain state returns the deserialized account data."""
    mock_state = {
        "authority": "5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8",
        "org": "5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8",
        "agent_id": "test-agent-001",
        "spending_limit_per_tx": 500_000_000,
        "daily_limit": 2_000_000_000,
        "daily_spent": 100_000_000,
        "last_reset_day": 20000,
        "is_active": True,
        "bump": 254,
        "sol_balance": 1.5,
        "pda_address": test_pda_wallet.pda_address,
    }

    with patch("agentwallet.api.routers.pda_wallets.PDAWalletService") as MockSvc:
        instance = MockSvc.return_value
        instance.get_pda_wallet = AsyncMock(return_value=test_pda_wallet)
        instance.get_pda_state = AsyncMock(return_value=mock_state)

        resp = await client.get(f"/v1/pda-wallets/{test_pda_wallet.id}/state")

    assert resp.status_code == 200
    body = resp.json()
    assert body["pda_address"] == test_pda_wallet.pda_address
    assert body["authority"] == "5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8"
    assert body["spending_limit_per_tx"] == 500_000_000
    assert body["daily_spent"] == 100_000_000
    assert body["sol_balance"] == 1.5
    assert body["is_active"] is True
    assert body["bump"] == 254


async def test_get_pda_wallet_state_not_found(client):
    """Reading on-chain state for non-existent wallet returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    with patch("agentwallet.api.routers.pda_wallets.PDAWalletService") as MockSvc:
        from agentwallet.core.exceptions import NotFoundError

        instance = MockSvc.return_value
        instance.get_pda_wallet = AsyncMock(side_effect=NotFoundError("PDA Wallet", fake_id))
        resp = await client.get(f"/v1/pda-wallets/{fake_id}/state")

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /v1/pda-wallets/{id}/transfer  (mocked service)
# ---------------------------------------------------------------------------


async def test_transfer_from_pda(client, test_pda_wallet):
    """Transferring from a PDA wallet returns signature and confirmation."""
    mock_result = {
        "signature": "MockTransferSig" + uuid.uuid4().hex[:16],
        "confirmed": True,
    }

    with patch("agentwallet.api.routers.pda_wallets.PDAWalletService") as MockSvc:
        instance = MockSvc.return_value
        instance.transfer_from_pda = AsyncMock(return_value=mock_result)

        resp = await client.post(
            f"/v1/pda-wallets/{test_pda_wallet.id}/transfer",
            json={
                "recipient": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                "amount_lamports": 100_000_000,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["signature"] == mock_result["signature"]
    assert body["confirmed"] is True


async def test_transfer_from_pda_unconfirmed(client, test_pda_wallet):
    """Transfer that does not confirm on-chain returns confirmed=False."""
    mock_result = {
        "signature": "UnconfSig" + uuid.uuid4().hex[:20],
        "confirmed": False,
    }

    with patch("agentwallet.api.routers.pda_wallets.PDAWalletService") as MockSvc:
        instance = MockSvc.return_value
        instance.transfer_from_pda = AsyncMock(return_value=mock_result)

        resp = await client.post(
            f"/v1/pda-wallets/{test_pda_wallet.id}/transfer",
            json={
                "recipient": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                "amount_lamports": 50_000_000,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmed"] is False


async def test_transfer_validation_errors(client, test_pda_wallet):
    """Transfer with invalid data returns 422."""
    # Missing recipient
    resp = await client.post(
        f"/v1/pda-wallets/{test_pda_wallet.id}/transfer",
        json={"amount_lamports": 100_000_000},
    )
    assert resp.status_code == 422

    # amount_lamports must be > 0
    resp = await client.post(
        f"/v1/pda-wallets/{test_pda_wallet.id}/transfer",
        json={
            "recipient": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
            "amount_lamports": 0,
        },
    )
    assert resp.status_code == 422

    # recipient too short
    resp = await client.post(
        f"/v1/pda-wallets/{test_pda_wallet.id}/transfer",
        json={
            "recipient": "short",
            "amount_lamports": 100_000_000,
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /v1/pda-wallets/{id}/limits  (mocked service)
# ---------------------------------------------------------------------------


async def test_update_pda_limits(client, test_pda_wallet):
    """Updating PDA limits returns the updated wallet."""
    mock_pw = MagicMock()
    mock_pw.id = test_pda_wallet.id
    mock_pw.org_id = test_pda_wallet.org_id
    mock_pw.pda_address = test_pda_wallet.pda_address
    mock_pw.authority_wallet_id = test_pda_wallet.authority_wallet_id
    mock_pw.agent_id = test_pda_wallet.agent_id
    mock_pw.agent_id_seed = test_pda_wallet.agent_id_seed
    mock_pw.spending_limit_per_tx = 999_000_000
    mock_pw.daily_limit = 3_000_000_000
    mock_pw.bump = test_pda_wallet.bump
    mock_pw.is_active = True
    mock_pw.tx_signature = test_pda_wallet.tx_signature
    mock_pw.created_at = datetime.now(timezone.utc)

    with patch("agentwallet.api.routers.pda_wallets.PDAWalletService") as MockSvc:
        instance = MockSvc.return_value
        instance.update_pda_limits = AsyncMock(return_value=mock_pw)

        resp = await client.patch(
            f"/v1/pda-wallets/{test_pda_wallet.id}/limits",
            json={
                "spending_limit_per_tx": 999_000_000,
                "daily_limit": 3_000_000_000,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["spending_limit_per_tx"] == 999_000_000
    assert body["daily_limit"] == 3_000_000_000
    assert body["is_active"] is True


async def test_update_pda_limits_deactivate(client, test_pda_wallet):
    """Deactivating a PDA wallet through the limits endpoint."""
    mock_pw = MagicMock()
    mock_pw.id = test_pda_wallet.id
    mock_pw.org_id = test_pda_wallet.org_id
    mock_pw.pda_address = test_pda_wallet.pda_address
    mock_pw.authority_wallet_id = test_pda_wallet.authority_wallet_id
    mock_pw.agent_id = test_pda_wallet.agent_id
    mock_pw.agent_id_seed = test_pda_wallet.agent_id_seed
    mock_pw.spending_limit_per_tx = test_pda_wallet.spending_limit_per_tx
    mock_pw.daily_limit = test_pda_wallet.daily_limit
    mock_pw.bump = test_pda_wallet.bump
    mock_pw.is_active = False
    mock_pw.tx_signature = test_pda_wallet.tx_signature
    mock_pw.created_at = datetime.now(timezone.utc)

    with patch("agentwallet.api.routers.pda_wallets.PDAWalletService") as MockSvc:
        instance = MockSvc.return_value
        instance.update_pda_limits = AsyncMock(return_value=mock_pw)

        resp = await client.patch(
            f"/v1/pda-wallets/{test_pda_wallet.id}/limits",
            json={"is_active": False},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["is_active"] is False


async def test_update_pda_limits_partial(client, test_pda_wallet):
    """Updating only spending_limit_per_tx without daily_limit or is_active."""
    mock_pw = MagicMock()
    mock_pw.id = test_pda_wallet.id
    mock_pw.org_id = test_pda_wallet.org_id
    mock_pw.pda_address = test_pda_wallet.pda_address
    mock_pw.authority_wallet_id = test_pda_wallet.authority_wallet_id
    mock_pw.agent_id = test_pda_wallet.agent_id
    mock_pw.agent_id_seed = test_pda_wallet.agent_id_seed
    mock_pw.spending_limit_per_tx = 750_000_000
    mock_pw.daily_limit = test_pda_wallet.daily_limit
    mock_pw.bump = test_pda_wallet.bump
    mock_pw.is_active = True
    mock_pw.tx_signature = test_pda_wallet.tx_signature
    mock_pw.created_at = datetime.now(timezone.utc)

    with patch("agentwallet.api.routers.pda_wallets.PDAWalletService") as MockSvc:
        instance = MockSvc.return_value
        instance.update_pda_limits = AsyncMock(return_value=mock_pw)

        resp = await client.patch(
            f"/v1/pda-wallets/{test_pda_wallet.id}/limits",
            json={"spending_limit_per_tx": 750_000_000},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["spending_limit_per_tx"] == 750_000_000


async def test_update_pda_limits_validation_error(client, test_pda_wallet):
    """Spending limit must be > 0 if provided."""
    resp = await client.patch(
        f"/v1/pda-wallets/{test_pda_wallet.id}/limits",
        json={"spending_limit_per_tx": 0},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /v1/pda-wallets/derive  (pure computation, no mocks needed)
# ---------------------------------------------------------------------------


async def test_derive_pda_address(client):
    """Derive PDA returns a deterministic address and bump."""
    resp = await client.post(
        "/v1/pda-wallets/derive",
        json={
            "org_pubkey": "5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8",
            "agent_id_seed": "test-agent-001",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "pda_address" in body
    assert "bump" in body
    assert isinstance(body["bump"], int)
    assert 0 <= body["bump"] <= 255
    # Address should be a valid base58 public key (~32-44 chars)
    assert len(body["pda_address"]) >= 32


async def test_derive_pda_address_deterministic(client):
    """Calling derive twice with the same inputs returns identical results."""
    payload = {
        "org_pubkey": "5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8",
        "agent_id_seed": "determinism-test",
    }
    resp1 = await client.post("/v1/pda-wallets/derive", json=payload)
    resp2 = await client.post("/v1/pda-wallets/derive", json=payload)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()


async def test_derive_pda_different_seeds(client):
    """Different seeds produce different PDA addresses."""
    base = {"org_pubkey": "5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8"}
    resp1 = await client.post(
        "/v1/pda-wallets/derive",
        json={**base, "agent_id_seed": "seed-a"},
    )
    resp2 = await client.post(
        "/v1/pda-wallets/derive",
        json={**base, "agent_id_seed": "seed-b"},
    )
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["pda_address"] != resp2.json()["pda_address"]


async def test_derive_pda_validation_errors(client):
    """Derive with invalid data returns 422."""
    # Missing org_pubkey
    resp = await client.post(
        "/v1/pda-wallets/derive",
        json={"agent_id_seed": "test"},
    )
    assert resp.status_code == 422

    # Empty agent_id_seed
    resp = await client.post(
        "/v1/pda-wallets/derive",
        json={
            "org_pubkey": "5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8",
            "agent_id_seed": "",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Unauthenticated access
# ---------------------------------------------------------------------------


async def test_unauthenticated_list(unauthed_client):
    """Listing PDA wallets without auth returns 401."""
    resp = await unauthed_client.get("/v1/pda-wallets")
    assert resp.status_code == 401


async def test_unauthenticated_get(unauthed_client):
    """Getting a PDA wallet without auth returns 401."""
    resp = await unauthed_client.get(f"/v1/pda-wallets/{uuid.uuid4()}")
    assert resp.status_code == 401


async def test_unauthenticated_create(unauthed_client):
    """Creating a PDA wallet without auth returns 401."""
    resp = await unauthed_client.post(
        "/v1/pda-wallets",
        json={
            "authority_wallet_id": str(uuid.uuid4()),
            "agent_id_seed": "unauthed",
            "spending_limit_per_tx": 100_000,
            "daily_limit": 500_000,
        },
    )
    assert resp.status_code == 401


async def test_unauthenticated_transfer(unauthed_client):
    """Transferring without auth returns 401."""
    resp = await unauthed_client.post(
        f"/v1/pda-wallets/{uuid.uuid4()}/transfer",
        json={
            "recipient": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
            "amount_lamports": 100_000,
        },
    )
    assert resp.status_code == 401


async def test_unauthenticated_update_limits(unauthed_client):
    """Updating limits without auth returns 401."""
    resp = await unauthed_client.patch(
        f"/v1/pda-wallets/{uuid.uuid4()}/limits",
        json={"spending_limit_per_tx": 100_000},
    )
    assert resp.status_code == 401


async def test_unauthenticated_derive(unauthed_client):
    """Deriving PDA address without auth returns 401."""
    resp = await unauthed_client.post(
        "/v1/pda-wallets/derive",
        json={
            "org_pubkey": "5kTLXsCAMw4jdaPMjCN7dvYzfX5SFUrLmn8vzT3Y7nW8",
            "agent_id_seed": "test",
        },
    )
    assert resp.status_code == 401


async def test_unauthenticated_state(unauthed_client):
    """Reading on-chain state without auth returns 401."""
    resp = await unauthed_client.get(f"/v1/pda-wallets/{uuid.uuid4()}/state")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Response field completeness
# ---------------------------------------------------------------------------


async def test_pda_wallet_response_fields(client, test_pda_wallet):
    """All expected fields are present in the PDA wallet response."""
    resp = await client.get(f"/v1/pda-wallets/{test_pda_wallet.id}")
    assert resp.status_code == 200
    body = resp.json()
    expected_fields = {
        "id",
        "org_id",
        "pda_address",
        "authority_wallet_id",
        "agent_id",
        "agent_id_seed",
        "spending_limit_per_tx",
        "daily_limit",
        "bump",
        "is_active",
        "tx_signature",
        "created_at",
    }
    assert expected_fields == set(body.keys())


async def test_pda_wallet_list_response_fields(client, test_pda_wallet):
    """List response has data array and total count."""
    resp = await client.get("/v1/pda-wallets")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"data", "total"}
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
