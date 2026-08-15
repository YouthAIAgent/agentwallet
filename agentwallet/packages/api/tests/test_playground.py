"""Tests for the Devnet Playground endpoints."""

import uuid

import pytest
from solders.keypair import Keypair

FAKE_SIG = "5f2k8Xy3Qm1vR9tW4nB7cJ6pHd2LzS0aG8eK3uYq1TvN"


def _fake_platform_kp() -> Keypair:
    return Keypair()  # random valid keypair


@pytest.mark.asyncio
async def test_playground_status(client, test_wallet, monkeypatch):
    """GET /playground returns the org wallet + a balance."""

    async def fake_balance(_client, address: str) -> int:
        return 5_000_000_000  # 5 SOL

    import agentwallet.api.routers.playground as pg

    monkeypatch.setattr(pg.solana, "get_balance", fake_balance)

    resp = await client.get("/v1/playground")
    assert resp.status_code == 200
    data = resp.json()
    assert data["wallet_address"]
    assert data["balance_sol"] == 5.0
    assert data["network"] == "devnet"


@pytest.mark.asyncio
async def test_playground_fund(client, test_wallet, monkeypatch):
    """POST /playground/fund transfers devnet SOL from the platform wallet."""
    import agentwallet.api.routers.playground as pg

    async def fake_balance(_client, address: str) -> int:
        return 100_000_000_000  # 100 SOL

    async def fake_transfer(client, from_keypair, to_address, lamports, fee_lamports=0, fee_recipient=None):
        assert lamports == int(0.01 * 1e9)
        return FAKE_SIG

    async def fake_confirm(_client, sig: str) -> bool:
        assert sig == FAKE_SIG
        return True

    monkeypatch.setattr(pg.solana, "get_balance", fake_balance)
    monkeypatch.setattr(pg.solana, "transfer_sol", fake_transfer)
    monkeypatch.setattr(pg.solana, "confirm_transaction", fake_confirm)
    monkeypatch.setattr(pg.solana, "load_platform_keypair", _fake_platform_kp)
    monkeypatch.setattr(pg, "_fund_cooldown", {})

    resp = await client.post("/v1/playground/fund")
    assert resp.status_code == 201
    data = resp.json()
    assert data["signature"] == FAKE_SIG
    assert data["confirmed"] is True
    assert "explorer.solana.com/tx/" in data["explorer_url"]
    assert data["amount_sol"] == 0.01


@pytest.mark.asyncio
async def test_playground_fund_cooldown(client, test_wallet, monkeypatch):
    """Second fund within the cooldown window is rejected (429)."""
    import agentwallet.api.routers.playground as pg

    async def fake_balance(_client, address: str) -> int:
        return 100_000_000_000

    async def fake_transfer(client, from_keypair, to_address, lamports, fee_lamports=0, fee_recipient=None):
        return FAKE_SIG

    async def fake_confirm(_client, sig: str) -> bool:
        return True

    monkeypatch.setattr(pg.solana, "get_balance", fake_balance)
    monkeypatch.setattr(pg.solana, "transfer_sol", fake_transfer)
    monkeypatch.setattr(pg.solana, "confirm_transaction", fake_confirm)
    monkeypatch.setattr(pg.solana, "load_platform_keypair", _fake_platform_kp)
    monkeypatch.setattr(pg, "_fund_cooldown", {})
    monkeypatch.setattr(pg.time, "monotonic", lambda: 100.0)

    first = await client.post("/v1/playground/fund")
    assert first.status_code == 201
    second = await client.post("/v1/playground/fund")
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_playground_x402_demo(client, test_wallet, monkeypatch):
    """POST /playground/x402 pays, verifies on-chain, and returns an AI response."""
    import agentwallet.api.routers.playground as pg

    class FakeTx:
        signature = FAKE_SIG
        status = "submitted"
        error = None

    class FakeEngine:
        def __init__(self, db):
            self.db = db

        async def transfer_sol(self, **kwargs):
            assert kwargs["amount_lamports"] == int(0.0001 * 1e9)
            assert "x402:playground:" in kwargs["idempotency_key"]
            return FakeTx()

    async def fake_verify(payment_header, expected_pay_to, expected_amount_lamports=None, **kw):
        assert expected_amount_lamports == int(0.0001 * 1e9)
        return {"valid": True, "error": None}

    async def fake_llm(prompt):
        return ("demo", "demo-model", "demo answer")

    monkeypatch.setattr(pg, "TransactionEngine", FakeEngine)
    monkeypatch.setattr(pg, "verify_payment_proof", fake_verify)
    monkeypatch.setattr(pg, "_call_demo_llm", fake_llm)

    resp = await client.post("/v1/playground/x402")
    assert resp.status_code == 201
    data = resp.json()
    assert data["payment_signature"] == FAKE_SIG
    assert data["verified_on_chain"] is True
    assert data["ai_provider"] == "demo"
    assert "explorer.solana.com/tx/" in data["payment_explorer_url"]
    assert data["amount_sol"] == 0.0001


@pytest.mark.asyncio
async def test_playground_x402_demo_no_signature(client, test_wallet, monkeypatch):
    """x402 demo without a signed transaction is rejected (400)."""
    import agentwallet.api.routers.playground as pg

    class FakeTx:
        signature = None
        status = "pending"
        error = None

    class FakeEngine:
        def __init__(self, db):
            self.db = db

        async def transfer_sol(self, **kwargs):
            return FakeTx()

    monkeypatch.setattr(pg, "TransactionEngine", FakeEngine)

    resp = await client.post("/v1/playground/x402")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_playground_transfer_insufficient(client, test_wallet, monkeypatch):
    """POST /playground/transfer without balance is rejected."""
    import agentwallet.api.routers.playground as pg

    async def fake_balance(_client, address: str) -> int:
        return 0

    class FakeManager:
        def __init__(self, db):
            self.db = db

        def _decrypt_keypair(self, wallet):
            return _fake_platform_kp()

    monkeypatch.setattr(pg.solana, "get_balance", fake_balance)
    monkeypatch.setattr(pg, "WalletManager", FakeManager)

    resp = await client.post("/v1/playground/transfer")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_playground_usdc(client, test_wallet, monkeypatch):
    """POST /playground/usdc mints devnet dUSDC to the org wallet."""
    import agentwallet.api.routers.playground as pg

    async def fake_mint(client, mint_authority_keypair, mint, owner_address, amount_raw, confirm=False):
        assert amount_raw == int(200.0 * 1e6)
        assert owner_address == test_wallet.address
        return FAKE_SIG

    monkeypatch.setattr(pg.solana, "mint_spl_token", fake_mint)
    monkeypatch.setattr(pg.solana, "load_platform_keypair", _fake_platform_kp)
    monkeypatch.setattr(pg, "_usdc_cooldown", {})

    resp = await client.post("/v1/playground/usdc")
    assert resp.status_code == 201
    data = resp.json()
    assert data["signature"] == FAKE_SIG
    assert data["confirmed"] is True
    assert data["amount_usdc"] == 200.0
    assert "explorer.solana.com/tx/" in data["explorer_url"]


@pytest.mark.asyncio
async def test_playground_usdc_cooldown(client, test_wallet, monkeypatch):
    """Second USDC grant within the cooldown window is rejected (429)."""
    import agentwallet.api.routers.playground as pg

    async def fake_mint(client, mint_authority_keypair, mint, owner_address, amount_raw, confirm=False):
        return FAKE_SIG

    monkeypatch.setattr(pg.solana, "mint_spl_token", fake_mint)
    monkeypatch.setattr(pg.solana, "load_platform_keypair", _fake_platform_kp)
    monkeypatch.setattr(pg, "_usdc_cooldown", {})
    monkeypatch.setattr(pg.time, "monotonic", lambda: 200.0)

    first = await client.post("/v1/playground/usdc")
    assert first.status_code == 201
    second = await client.post("/v1/playground/usdc")
    assert second.status_code == 429
    assert "try again in" in second.json()["detail"]


@pytest.mark.asyncio
async def test_playground_usdc_daily_limit(client, test_wallet, monkeypatch):
    """USDC grant past the rolling 24h cap is rejected (429) with a daily hint."""
    import agentwallet.api.routers.playground as pg

    async def fake_mint(client, mint_authority_keypair, mint, owner_address, amount_raw, confirm=False):
        return FAKE_SIG

    monkeypatch.setattr(pg.solana, "mint_spl_token", fake_mint)
    monkeypatch.setattr(pg.solana, "load_platform_keypair", _fake_platform_kp)
    monkeypatch.setattr(pg, "_usdc_cooldown", {})
    monkeypatch.setattr(pg.time, "monotonic", lambda: 500.0)
    # Already used the daily allotment in the past hour
    monkeypatch.setattr(
        pg, "_usdc_daily", {str(test_wallet.org_id): [100.0] * pg.USDC_DAILY_LIMIT}
    )

    resp = await client.post("/v1/playground/usdc")
    assert resp.status_code == 429
    assert "daily devnet usdc limit" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_playground_fund_daily_limit(client, test_wallet, monkeypatch):
    """Fund past the rolling 24h cap is rejected (429) with a daily hint."""
    import agentwallet.api.routers.playground as pg

    async def fake_transfer(client, from_keypair, to_address, lamports):
        return FAKE_SIG

    async def fake_confirm(client, sig):
        return True

    async def fake_balance(client, addr):
        return 10_000_000_000  # 10 SOL, plenty

    monkeypatch.setattr(pg.solana, "transfer_sol", fake_transfer)
    monkeypatch.setattr(pg.solana, "confirm_transaction", fake_confirm)
    monkeypatch.setattr(pg.solana, "get_balance", fake_balance)
    monkeypatch.setattr(pg.solana, "load_platform_keypair", _fake_platform_kp)
    monkeypatch.setattr(pg, "_fund_cooldown", {})
    monkeypatch.setattr(pg.time, "monotonic", lambda: 600.0)
    monkeypatch.setattr(
        pg, "_fund_daily", {str(test_wallet.org_id): [100.0] * pg.FUND_DAILY_LIMIT}
    )

    resp = await client.post("/v1/playground/fund")
    assert resp.status_code == 429
    assert "daily devnet sol limit" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_playground_escrow_refund(client, test_wallet, monkeypatch):
    """POST /playground/escrow/{id}/refund refunds escrow funds to the funder wallet."""
    import agentwallet.api.routers.playground as pg

    escrow_id = uuid.uuid4()

    class FakeEscrow:
        id = escrow_id
        status = "refunded"
        refund_signature = FAKE_SIG
        funder_wallet_id = None
        recipient_address = "recv-addr"

    async def fake_refund(self, requested_id, org_id):
        assert str(requested_id) == str(escrow_id)
        return FakeEscrow()

    monkeypatch.setattr(pg.EscrowService, "refund_escrow", fake_refund)

    resp = await client.post(f"/v1/playground/escrow/{escrow_id}/refund")
    assert resp.status_code == 200
    data = resp.json()
    assert data["escrow_id"] == str(escrow_id)
    assert data["status"] == "refunded"
    assert data["refund_signature"] == FAKE_SIG
    assert "explorer.solana.com/tx/" in data["refund_explorer_url"]
