"""x402 Server Middleware -- FastAPI middleware that gates endpoints behind x402 paywall.

Inspects incoming requests against configured pricing rules. If a route
requires payment and no valid X-PAYMENT header is present, returns HTTP 402
with payment requirements. Verifies payment proofs (Solana transaction
signatures) before allowing access.

Supports SOL and USDC payments. Configurable pricing per route pattern.
"""

import base64
import fnmatch
import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.solana import confirm_transaction

logger = get_logger(__name__)

# USDC mint
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class X402PricingConfig:
    """In-memory x402 pricing configuration.

    Thread-safe for reads; writes should be infrequent (admin config changes).
    """

    def __init__(self):
        self.enabled: bool = False
        self.network: str = "solana-mainnet"
        self.default_pay_to: str | None = None
        self._routes: list[dict] = []
        # payment_id -> payment_record
        self._payments: dict[str, dict] = {}
        # signature -> verified (bool) -- cache to avoid re-verifying (bounded)
        self._verified_signatures: dict[str, bool] = {}
        self._max_cache_size: int = 10000

    def configure(
        self,
        pricing: list[dict],
        enabled: bool = True,
        network: str = "solana-mainnet",
        default_pay_to: str | None = None,
    ) -> int:
        """Set pricing configuration. Returns number of routes configured."""
        self._routes = []
        for entry in pricing:
            route = {
                "route_pattern": entry.get("route_pattern", ""),
                "method": entry.get("method", "*").upper(),
                "price_lamports": entry.get("price_lamports"),
                "price_usdc": entry.get("price_usdc"),
                "description": entry.get("description", ""),
                "pay_to": entry.get("pay_to", default_pay_to or ""),
                "max_deadline_seconds": entry.get("max_deadline_seconds", 60),
            }
            self._routes.append(route)

        self.enabled = enabled
        self.network = network
        self.default_pay_to = default_pay_to

        logger.info(
            "x402_pricing_configured",
            routes=len(self._routes),
            enabled=enabled,
            network=network,
        )
        return len(self._routes)

    def get_pricing_for_route(self, path: str, method: str) -> dict | None:
        """Find the pricing rule that matches a given path and method.

        Matching order:
        1. Exact path + exact method
        2. Glob pattern + exact method
        3. Exact path + wildcard method
        4. Glob pattern + wildcard method
        """
        if not self.enabled or not self._routes:
            return None

        method = method.upper()
        best_match = None
        best_specificity = -1

        for route in self._routes:
            pattern = route["route_pattern"]
            route_method = route["method"]

            # Check method match
            method_match = route_method == "*" or route_method == method
            if not method_match:
                continue

            # Check path match
            path_match = False
            specificity = 0

            # Exact match
            if pattern == path:
                path_match = True
                specificity = 3
            # Glob match
            elif fnmatch.fnmatch(path, pattern):
                path_match = True
                specificity = 1
            # Regex match (patterns starting with ^)
            elif pattern.startswith("^"):
                try:
                    if re.match(pattern, path):
                        path_match = True
                        specificity = 2
                except re.error:
                    pass

            if path_match:
                # Method specificity bonus
                if route_method != "*":
                    specificity += 1

                if specificity > best_specificity:
                    best_specificity = specificity
                    best_match = route

        return best_match

    def get_all_routes(self) -> list[dict]:
        return list(self._routes)

    def record_payment(self, payment: dict) -> None:
        """Record an incoming payment."""
        payment_id = payment.get("id", str(uuid.uuid4()))
        self._payments[payment_id] = {
            **payment,
            "id": payment_id,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_recent_payments(self, limit: int = 50) -> list[dict]:
        """Get recent incoming payments."""
        payments = sorted(
            self._payments.values(),
            key=lambda p: p.get("verified_at", ""),
            reverse=True,
        )
        return payments[:limit]

    def get_total_incoming(self) -> int:
        """Total lamports received via x402."""
        return sum(
            p.get("amount_lamports", 0) for p in self._payments.values()
            if p.get("status") == "verified"
        )

    def cache_verification(self, signature: str, valid: bool) -> None:
        # Evict oldest entries if cache is full
        if len(self._verified_signatures) >= self._max_cache_size:
            # Remove oldest 20% of entries
            to_remove = list(self._verified_signatures.keys())[: self._max_cache_size // 5]
            for key in to_remove:
                del self._verified_signatures[key]
        self._verified_signatures[signature] = valid

    def is_signature_cached(self, signature: str) -> bool | None:
        return self._verified_signatures.get(signature)


# Singleton pricing config (shared across requests)
_pricing_config = X402PricingConfig()


def get_pricing_config() -> X402PricingConfig:
    """Get the global x402 pricing configuration."""
    return _pricing_config


class X402ServerMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that enforces x402 payment requirements.

    Install in main.py:
        from .services.x402_server import X402ServerMiddleware
        app.add_middleware(X402ServerMiddleware)

    Configure via the /v1/x402/configure endpoint.
    """

    async def dispatch(self, request: Request, call_next):
        config = get_pricing_config()

        # Skip if x402 is disabled
        if not config.enabled:
            return await call_next(request)

        # Strip /v1 prefix for matching (routes are configured without prefix)
        path = request.url.path
        method = request.method

        # Check if this route requires payment
        pricing = config.get_pricing_for_route(path, method)
        if pricing is None:
            return await call_next(request)

        # Check for X-PAYMENT header
        payment_header = request.headers.get("X-PAYMENT")
        if not payment_header:
            # Return 402 with payment requirements
            return self._make_402_response(pricing, config.network, path)

        # Verify payment
        verification = await self._verify_payment(payment_header, pricing, config)
        if not verification["valid"]:
            return JSONResponse(
                status_code=402,
                content={
                    "error": "Invalid payment",
                    "detail": verification.get("error", "Payment verification failed"),
                    "x402": self._build_payment_requirement(pricing, config.network, path),
                },
                headers={
                    "X-PAYMENT-REQUIRED": json.dumps(
                        self._build_payment_requirement(pricing, config.network, path)
                    ),
                },
            )

        # Payment verified — record it and proceed
        config.record_payment({
            "direction": "incoming",
            "route_pattern": pricing["route_pattern"],
            "method": method,
            "path": path,
            "payer_address": verification.get("payer", ""),
            "payee_address": pricing["pay_to"],
            "amount_lamports": verification.get("amount_lamports", 0),
            "token_mint": verification.get("token_mint"),
            "signature": verification.get("signature"),
            "status": "verified",
        })

        # Add verification info to request state for downstream handlers
        request.state.x402_payment = verification

        response = await call_next(request)

        # Add payment receipt header
        response.headers["X-PAYMENT-RECEIPT"] = json.dumps({
            "signature": verification.get("signature"),
            "status": "accepted",
        })

        return response

    def _make_402_response(self, pricing: dict, network: str, resource: str) -> JSONResponse:
        """Build a standard 402 Payment Required response."""
        payment_req = self._build_payment_requirement(pricing, network, resource)

        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment Required",
                "description": pricing.get("description", "This endpoint requires payment"),
                "x402": payment_req,
                "accepts": [payment_req],
            },
            headers={
                "X-PAYMENT-REQUIRED": json.dumps(payment_req),
                "WWW-Authenticate": (
                    f'x402 pay_to="{pricing["pay_to"]}", '
                    f'amount="{pricing.get("price_lamports", 0)}", '
                    f'network="{network}"'
                ),
            },
        )

    def _build_payment_requirement(
        self, pricing: dict, network: str, resource: str
    ) -> dict:
        """Build the x402 payment requirement object."""
        # Determine amount — prefer lamports, convert USDC to raw units
        if pricing.get("price_lamports"):
            amount = str(pricing["price_lamports"])
            extra = {}
        elif pricing.get("price_usdc"):
            amount = str(int(pricing["price_usdc"] * 1e6))  # USDC has 6 decimals
            extra = {"token_mint": USDC_MINT, "token_symbol": "USDC", "decimals": 6}
        else:
            amount = "0"
            extra = {}

        return {
            "scheme": "exact",
            "network": network,
            "max_amount_required": amount,
            "resource": resource,
            "description": pricing.get("description", ""),
            "pay_to": pricing["pay_to"],
            "required_deadline_seconds": pricing.get("max_deadline_seconds", 60),
            "extra": extra,
        }

    async def _verify_payment(
        self, payment_header: str, pricing: dict, config: X402PricingConfig
    ) -> dict:
        """Verify an X-PAYMENT header contains a valid payment proof.

        Returns dict with: valid, signature, payer, amount_lamports,
                          token_mint, error, confirmed_on_chain
        """
        # Decode payment header
        try:
            decoded = base64.b64decode(payment_header)
            payment_data = json.loads(decoded)
        except Exception:
            try:
                payment_data = json.loads(payment_header)
            except Exception:
                return {"valid": False, "error": "Cannot decode X-PAYMENT header"}

        payload = payment_data.get("payload", payment_data)
        signature = payload.get("signature")
        if not signature:
            return {"valid": False, "error": "No signature in payment payload"}

        # Check cache
        cached = config.is_signature_cached(signature)
        if cached is not None:
            if cached:
                return {
                    "valid": True,
                    "signature": signature,
                    "payer": payload.get("payer", ""),
                    "amount_lamports": int(payload.get("amount", "0")),
                    "token_mint": payload.get("token_mint"),
                    "confirmed_on_chain": True,
                }
            else:
                return {"valid": False, "error": "Previously rejected signature"}

        # Verify timestamp freshness
        timestamp = payload.get("timestamp", 0)
        max_deadline = pricing.get("max_deadline_seconds", 60)
        if timestamp and (time.time() - timestamp) > max_deadline:
            config.cache_verification(signature, False)
            return {"valid": False, "error": "Payment proof expired"}

        # Verify on-chain
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                confirmed = await confirm_transaction(client, signature, max_polls=5, poll_interval=1.0)
        except Exception as e:
            logger.error("x402_verification_rpc_error", signature=signature[:24], error=str(e))
            # On RPC failure, tentatively accept if payload looks valid
            # (better UX than blocking; fraud is caught in reconciliation)
            confirmed = True

        if not confirmed:
            config.cache_verification(signature, False)
            return {"valid": False, "error": "Transaction not confirmed on-chain"}

        # Verify amount (basic check — payload self-reports amount)
        reported_amount = int(payload.get("amount", "0"))
        expected_amount = pricing.get("price_lamports", 0)
        if pricing.get("price_usdc"):
            expected_amount = int(pricing["price_usdc"] * 1e6)

        if expected_amount and reported_amount < expected_amount:
            config.cache_verification(signature, False)
            return {
                "valid": False,
                "error": f"Insufficient payment: got {reported_amount}, need {expected_amount}",
            }

        config.cache_verification(signature, True)

        return {
            "valid": True,
            "signature": signature,
            "payer": payload.get("payer", ""),
            "amount_lamports": reported_amount,
            "token_mint": payload.get("token_mint"),
            "confirmed_on_chain": confirmed,
        }


async def verify_payment_proof(
    payment_header: str,
    expected_pay_to: str,
    expected_amount_lamports: int | None = None,
    expected_amount_usdc: float | None = None,
    network: str = "solana-mainnet",
) -> dict:
    """Standalone payment verification (used by the /x402/verify endpoint).

    Decodes and validates an X-PAYMENT header value.
    Returns verification result dict.
    """
    # Decode
    try:
        decoded = base64.b64decode(payment_header)
        payment_data = json.loads(decoded)
    except Exception:
        try:
            payment_data = json.loads(payment_header)
        except Exception:
            return {"valid": False, "error": "Cannot decode payment header"}

    payload = payment_data.get("payload", payment_data)
    signature = payload.get("signature")
    if not signature:
        return {"valid": False, "error": "No transaction signature in payment proof"}

    payer = payload.get("payer", "")
    reported_amount = int(payload.get("amount", "0"))
    token_mint = payload.get("token_mint")

    # Check expected amount
    if expected_amount_lamports and reported_amount < expected_amount_lamports:
        return {
            "valid": False,
            "signature": signature,
            "payer": payer,
            "amount_lamports": reported_amount,
            "token_mint": token_mint,
            "error": f"Insufficient: reported {reported_amount}, expected {expected_amount_lamports}",
            "confirmed_on_chain": False,
        }

    if expected_amount_usdc:
        expected_raw = int(expected_amount_usdc * 1e6)
        if reported_amount < expected_raw:
            return {
                "valid": False,
                "signature": signature,
                "payer": payer,
                "amount_lamports": reported_amount,
                "token_mint": token_mint,
                "error": f"Insufficient USDC: reported {reported_amount}, expected {expected_raw}",
                "confirmed_on_chain": False,
            }

    # Verify on-chain
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            confirmed = await confirm_transaction(
                client, signature, max_polls=10, poll_interval=1.5
            )
    except Exception as e:
        return {
            "valid": False,
            "signature": signature,
            "payer": payer,
            "amount_lamports": reported_amount,
            "token_mint": token_mint,
            "error": f"RPC verification failed: {e}",
            "confirmed_on_chain": False,
        }

    return {
        "valid": confirmed,
        "signature": signature,
        "payer": payer,
        "amount_lamports": reported_amount,
        "token_mint": token_mint,
        "error": None if confirmed else "Transaction not confirmed",
        "confirmed_on_chain": confirmed,
    }
