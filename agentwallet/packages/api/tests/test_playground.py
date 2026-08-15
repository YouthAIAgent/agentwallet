"""Tests for the Devnet Playground endpoints."""

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
        assert lamports == int(0.05 * 1e9)
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
    assert data["amount_sol"] == 0.05


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
