"""Tests for x402 payment gateway -- paywall middleware and router."""

import base64
import json
from unittest.mock import AsyncMock, patch

import pytest
from agentwallet.services.x402_server import get_pricing_config


@pytest.fixture(autouse=True)
def reset_x402_config():
    """Reset the global x402 pricing config + verification cache before/after each test."""
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


# ── Router: configure / status / verify ──────────────────────────────


@pytest.mark.asyncio
async def test_configure_x402_pricing(client):
    """Configure x402 pricing for a route."""
    resp = await client.post(
        "/v1/x402/configure",
        json={
            "pricing": [
                {
                    "route_pattern": "/agents/*",
                    "method": "GET",
                    "price_lamports": 100_000,
                    "description": "Pay to list agents",
                    "pay_to": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                }
            ],
            "enabled": True,
            "network": "solana-mainnet",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured_routes"] == 1
    assert data["enabled"] is True


@pytest.mark.asyncio
async def test_get_x402_status(client):
    """Status endpoint returns configured routes."""
    resp = await client.get("/v1/x402/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "server_pricing" in data
    assert "enabled" in data


@pytest.mark.asyncio
async def test_verify_x402_payment_valid(client):
    """Verify endpoint returns valid for a confirmed payment."""
    header = base64.b64encode(
        json.dumps(
            {
                "payload": {
                    "signature": "5" * 87,
                    "payer": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": "100000",
                    "timestamp": 9999999999,
                }
            }
        ).encode()
    ).decode()

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
        resp = await client.post(
            "/v1/x402/verify",
            json={
                "payment_header": header,
                "expected_pay_to": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                "expected_amount_lamports": 100_000,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["confirmed_on_chain"] is True


@pytest.mark.asyncio
async def test_verify_x402_payment_rejected(client):
    """Verify endpoint rejects payments where the on-chain recipient differs."""
    header = base64.b64encode(
        json.dumps(
            {
                "payload": {
                    "signature": "5" * 87,
                    "amount": "100000",
                    "timestamp": 9999999999,
                }
            }
        ).encode()
    ).decode()

    with (
        patch(
            "agentwallet.services.x402_server.confirm_transaction",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "agentwallet.services.x402_server.verify_transfer_on_chain",
            new=AsyncMock(
                return_value={
                    "valid": False,
                    "payer": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "payee": "SomeOtherAddress",
                    "amount": 100_000,
                    "token_mint": None,
                    "error": "Payee received 0, expected at least 100000",
                }
            ),
        ),
    ):
        resp = await client.post(
            "/v1/x402/verify",
            json={
                "payment_header": header,
                "expected_pay_to": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                "expected_amount_lamports": 100_000,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert data["error"] is not None


# ── Paywall middleware ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_paywall_disabled_by_default(client, test_agent):
    """With x402 disabled, requests pass through without payment."""
    resp = await client.get(f"/v1/agents/{test_agent.id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_paywall_returns_402_without_header(client, test_agent):
    """Enabled paywall returns 402 with spec-compliant payment requirements."""
    config = get_pricing_config()
    config.configure(
        pricing=[
            {
                "route_pattern": "/agents/*",
                "method": "GET",
                "price_lamports": 100_000,
                "description": "Pay to view agents",
                "pay_to": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
            }
        ],
        enabled=True,
        network="solana-mainnet",
    )

    resp = await client.get(f"/v1/agents/{test_agent.id}")
    assert resp.status_code == 402
    body = resp.json()
    assert body["x402Version"] == "1.0"
    assert "accepts" in body
    assert body["accepts"][0]["pay_to"] == "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3"
    assert body["accepts"][0]["amount"] == "100000"
    assert body["accepts"][0]["token_symbol"] == "SOL"
    assert resp.headers.get("X-PAYMENT-REQUIRED") is not None


@pytest.mark.asyncio
async def test_paywall_accepts_valid_payment(client, test_agent):
    """Valid X-PAYMENT proof passes the paywall (mocked on-chain verification)."""
    config = get_pricing_config()
    config.configure(
        pricing=[
            {
                "route_pattern": "/agents/*",
                "method": "GET",
                "price_lamports": 100_000,
                "description": "Pay to view agents",
                "pay_to": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
            }
        ],
        enabled=True,
        network="solana-mainnet",
    )

    proof = base64.b64encode(
        json.dumps(
            {
                "payload": {
                    "signature": "5" * 87,
                    "payer": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "amount": "100000",
                    "timestamp": 9999999999,
                }
            }
        ).encode()
    ).decode()

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
        resp = await client.get(
            f"/v1/agents/{test_agent.id}",
            headers={"X-PAYMENT": proof},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_paywall_rejects_insufficient_payment(client, test_agent):
    """Payment below the required amount is rejected."""
    config = get_pricing_config()
    config.configure(
        pricing=[
            {
                "route_pattern": "/agents/*",
                "method": "GET",
                "price_lamports": 1_000_000,
                "description": "Pay to view agents",
                "pay_to": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
            }
        ],
        enabled=True,
        network="solana-mainnet",
    )

    proof = base64.b64encode(
        json.dumps(
            {
                "payload": {
                    "signature": "5" * 87,
                    "amount": "100000",
                    "timestamp": 9999999999,
                }
            }
        ).encode()
    ).decode()

    with (
        patch(
            "agentwallet.services.x402_server.confirm_transaction",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "agentwallet.services.x402_server.verify_transfer_on_chain",
            new=AsyncMock(
                return_value={
                    "valid": False,
                    "payer": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "payee": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                    "amount": 100_000,
                    "token_mint": None,
                    "error": "Payee received 100000, expected at least 1000000",
                }
            ),
        ),
    ):
        resp = await client.get(
            f"/v1/agents/{test_agent.id}",
            headers={"X-PAYMENT": proof},
        )
    assert resp.status_code == 402
    body = resp.json()
    assert "Invalid payment" in body["error"]
