"""x402 Client Middleware -- HTTP client wrapper with auto-pay for 402 responses.

Detects HTTP 402 Payment Required responses, automatically creates and signs
Solana payment transactions, and retries the request with payment proof in
the X-PAYMENT header.

Integrates with WalletManager for signing, TransactionEngine for policy
enforcement, and TokenService for USDC transfers.
"""

import base64
import json
import time
import uuid
from datetime import date, datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.exceptions import (
    InsufficientBalanceError,
    PolicyDeniedError,
    ValidationError,
)
from ..core.logging import get_logger
from ..core.solana import get_balance, transfer_sol, confirm_transaction
from ..models.transaction import Transaction
from .token_service import TokenService
from .wallet_manager import WalletManager

logger = get_logger(__name__)

# USDC mint on mainnet/devnet
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class X402SpendingTracker:
    """Track per-domain / per-endpoint spending for limit enforcement."""

    def __init__(self):
        # domain -> {date_str -> total_lamports}
        self._daily_spend: dict[str, dict[str, int]] = {}
        # History of all payments
        self._history: list[dict] = []

    def record_payment(
        self,
        domain: str,
        url: str,
        amount_lamports: int,
        signature: str | None = None,
        token_mint: str | None = None,
    ) -> None:
        today = date.today().isoformat()
        if domain not in self._daily_spend:
            self._daily_spend[domain] = {}
        self._daily_spend[domain][today] = (
            self._daily_spend[domain].get(today, 0) + amount_lamports
        )
        self._history.append({
            "id": str(uuid.uuid4()),
            "domain": domain,
            "url": url,
            "amount_lamports": amount_lamports,
            "signature": signature,
            "token_mint": token_mint,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_daily_spend(self, domain: str) -> int:
        today = date.today().isoformat()
        return self._daily_spend.get(domain, {}).get(today, 0)

    def get_total_spend(self) -> int:
        return sum(p["amount_lamports"] for p in self._history)

    def get_history(self) -> list[dict]:
        return list(self._history)

    def check_limit(
        self,
        domain: str,
        amount_lamports: int,
        max_per_request_lamports: int | None = None,
        max_daily_lamports: int | None = None,
    ) -> tuple[bool, str | None]:
        """Check if a payment is within spending limits.

        Returns (allowed, denial_reason).
        """
        if max_per_request_lamports is not None and amount_lamports > max_per_request_lamports:
            return False, (
                f"Payment {amount_lamports} lamports exceeds per-request limit "
                f"of {max_per_request_lamports} lamports for {domain}"
            )

        if max_daily_lamports is not None:
            current = self.get_daily_spend(domain)
            if current + amount_lamports > max_daily_lamports:
                return False, (
                    f"Daily spend would be {current + amount_lamports} lamports, "
                    f"exceeding limit of {max_daily_lamports} for {domain}"
                )

        return True, None


class X402ClientMiddleware:
    """HTTP client wrapper that auto-pays for 402 Payment Required responses.

    Usage:
        middleware = X402ClientMiddleware(
            db=db,
            org_id=org_id,
            wallet_id=wallet_id,
        )
        response = await middleware.request("GET", "https://api.example.com/data")
        # If the server returns 402, middleware automatically:
        #   1. Parses payment requirements from response
        #   2. Validates spending limits
        #   3. Creates & signs Solana payment
        #   4. Retries with X-PAYMENT header
    """

    def __init__(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        org_tier: str,
        wallet_id: uuid.UUID,
        agent_id: uuid.UUID | None = None,
        spending_limits: dict[str, dict] | None = None,
        auto_pay: bool = True,
        max_retries: int = 1,
        http_timeout: float = 30.0,
    ):
        self.db = db
        self.org_id = org_id
        self.org_tier = org_tier
        self.wallet_id = wallet_id
        self.agent_id = agent_id
        self.auto_pay = auto_pay
        self.max_retries = max_retries
        self.http_timeout = http_timeout

        self.wallet_mgr = WalletManager(db)
        self.token_service = TokenService(db)
        self.tracker = X402SpendingTracker()

        # spending_limits: domain -> {max_per_request_lamports, max_daily_lamports, ...}
        self._spending_limits = spending_limits or {}

    async def request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        body: str | None = None,
        max_amount_lamports: int | None = None,
        max_amount_usdc: float | None = None,
    ) -> dict:
        """Make an HTTP request with automatic 402 payment handling.

        Returns dict with: status_code, headers, body, payment_made,
                          payment_signature, payment_amount_lamports
        """
        headers = dict(headers or {})

        async with httpx.AsyncClient(timeout=self.http_timeout) as client:
            # Make initial request
            response = await self._do_request(client, method, url, headers, body)

            if response.status_code != 402 or not self.auto_pay:
                return self._format_response(response)

            # Parse payment requirements from 402 response
            payment_req = self._parse_payment_requirements(response)
            if not payment_req:
                logger.warning("x402_no_payment_info", url=url)
                return self._format_response(response)

            # Extract domain for spending limits
            from urllib.parse import urlparse
            domain = urlparse(url).hostname or "unknown"

            # Determine payment amount
            amount_lamports = int(payment_req.get("max_amount_required", "0"))
            token_mint = payment_req.get("extra", {}).get("token_mint")

            # Apply per-call overrides
            if max_amount_lamports is not None and amount_lamports > max_amount_lamports:
                logger.warning(
                    "x402_amount_exceeds_caller_limit",
                    requested=amount_lamports,
                    limit=max_amount_lamports,
                )
                return self._format_response(response)

            if max_amount_usdc is not None and token_mint == USDC_MINT:
                max_usdc_raw = int(max_amount_usdc * 1e6)
                if amount_lamports > max_usdc_raw:
                    logger.warning(
                        "x402_usdc_amount_exceeds_limit",
                        requested=amount_lamports,
                        limit=max_usdc_raw,
                    )
                    return self._format_response(response)

            # Check spending limits
            domain_limits = self._spending_limits.get(domain, self._spending_limits.get("*", {}))
            allowed, reason = self.tracker.check_limit(
                domain=domain,
                amount_lamports=amount_lamports,
                max_per_request_lamports=domain_limits.get("max_per_request_lamports"),
                max_daily_lamports=domain_limits.get("max_daily_lamports"),
            )
            if not allowed:
                logger.warning("x402_spending_limit_exceeded", reason=reason, url=url)
                return self._format_response(response, error=reason)

            # Make payment
            pay_to = payment_req.get("pay_to", "")
            if not pay_to:
                logger.error("x402_no_pay_to_address", url=url)
                return self._format_response(response)

            payment_proof = await self._make_payment(
                pay_to=pay_to,
                amount_lamports=amount_lamports,
                token_mint=token_mint,
                resource=url,
            )
            if not payment_proof:
                logger.error("x402_payment_failed", url=url)
                return self._format_response(response)

            # Track the spend
            self.tracker.record_payment(
                domain=domain,
                url=url,
                amount_lamports=amount_lamports,
                signature=payment_proof.get("signature"),
                token_mint=token_mint,
            )

            # Retry with payment header
            payment_header = base64.b64encode(
                json.dumps({
                    "x402Version": 1,
                    "scheme": "exact",
                    "network": payment_req.get("network", "solana-mainnet"),
                    "payload": payment_proof,
                }).encode()
            ).decode()

            headers["X-PAYMENT"] = payment_header
            retry_response = await self._do_request(client, method, url, headers, body)

            result = self._format_response(retry_response)
            result["payment_made"] = True
            result["payment_signature"] = payment_proof.get("signature")
            result["payment_amount_lamports"] = amount_lamports
            return result

    async def _do_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: dict,
        body: str | None,
    ) -> httpx.Response:
        """Execute the actual HTTP request."""
        kwargs: dict[str, Any] = {"headers": headers}
        if body and method.upper() in ("POST", "PUT", "PATCH"):
            kwargs["content"] = body
        return await client.request(method, url, **kwargs)

    def _parse_payment_requirements(self, response: httpx.Response) -> dict | None:
        """Extract x402 payment requirements from a 402 response.

        Checks:
        1. X-PAYMENT-REQUIRED header (JSON or base64-encoded JSON)
        2. Response body JSON with 'x402' key
        3. WWW-Authenticate header with x402 scheme
        """
        # Check X-PAYMENT-REQUIRED header
        payment_header = response.headers.get("X-PAYMENT-REQUIRED")
        if payment_header:
            try:
                return json.loads(payment_header)
            except json.JSONDecodeError:
                try:
                    decoded = base64.b64decode(payment_header)
                    return json.loads(decoded)
                except Exception:
                    pass

        # Check response body
        try:
            body = response.json()
            if isinstance(body, dict):
                # Direct x402 format
                if "x402" in body:
                    return body["x402"]
                # Standard format with required fields
                if "pay_to" in body and "max_amount_required" in body:
                    return body
                # Accepts array format (first entry)
                if "accepts" in body and isinstance(body["accepts"], list) and body["accepts"]:
                    return body["accepts"][0]
        except Exception:
            pass

        # Check WWW-Authenticate header
        www_auth = response.headers.get("WWW-Authenticate", "")
        if "x402" in www_auth.lower():
            # Parse key=value pairs
            parts = {}
            for part in www_auth.split(","):
                part = part.strip()
                if "=" in part:
                    key, val = part.split("=", 1)
                    parts[key.strip().lower()] = val.strip().strip('"')
            if "pay_to" in parts:
                return parts

        return None

    async def _make_payment(
        self,
        pay_to: str,
        amount_lamports: int,
        token_mint: str | None = None,
        resource: str = "",
    ) -> dict | None:
        """Create and submit a Solana payment transaction.

        Returns payment proof dict or None on failure.
        """
        try:
            wallet = await self.wallet_mgr.get_wallet(self.wallet_id, self.org_id)
            keypair = self.wallet_mgr._decrypt_keypair(wallet)

            if token_mint and token_mint == USDC_MINT:
                # USDC payment
                signature = await self._transfer_usdc(
                    keypair=keypair,
                    to_address=pay_to,
                    amount_raw=amount_lamports,  # For USDC, amount is in raw token units
                )
            else:
                # SOL payment
                async with httpx.AsyncClient(timeout=15) as client:
                    settings = get_settings()
                    signature = await transfer_sol(
                        client=client,
                        from_keypair=keypair,
                        to_address=pay_to,
                        lamports=amount_lamports,
                    )

            # Record transaction in DB
            tx_record = Transaction(
                org_id=self.org_id,
                agent_id=self.agent_id,
                wallet_id=self.wallet_id,
                tx_type="x402_payment",
                status="submitted",
                from_address=str(keypair.pubkey()),
                to_address=pay_to,
                amount_lamports=amount_lamports,
                token_mint=token_mint,
                memo=f"x402 payment for {resource[:100]}",
            )
            self.db.add(tx_record)
            await self.db.flush()

            logger.info(
                "x402_payment_sent",
                signature=signature[:24] if signature else "none",
                amount=amount_lamports,
                pay_to=pay_to[:16],
                resource=resource[:64],
            )

            return {
                "signature": signature,
                "payer": str(keypair.pubkey()),
                "amount": str(amount_lamports),
                "token_mint": token_mint,
                "timestamp": int(time.time()),
            }

        except InsufficientBalanceError as e:
            logger.warning("x402_insufficient_balance", error=str(e))
            return None
        except PolicyDeniedError as e:
            logger.warning("x402_policy_denied", error=str(e))
            return None
        except Exception as e:
            logger.error("x402_payment_error", error=str(e))
            return None

    async def _transfer_usdc(
        self,
        keypair,
        to_address: str,
        amount_raw: int,
    ) -> str:
        """Transfer USDC using the Solana SPL token program."""
        from ..core.solana import transfer_spl_token

        async with httpx.AsyncClient(timeout=15) as client:
            return await transfer_spl_token(
                client=client,
                from_keypair=keypair,
                to_address=to_address,
                mint=USDC_MINT,
                amount=amount_raw,
            )

    def _format_response(
        self,
        response: httpx.Response,
        error: str | None = None,
    ) -> dict:
        """Format HTTP response into a standard dict."""
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "payment_made": False,
            "payment_signature": None,
            "payment_amount_lamports": None,
        }
        if error:
            result["error"] = error
        return result

    def get_spending_summary(self) -> dict:
        """Get a summary of all x402 spending."""
        return {
            "total_lamports": self.tracker.get_total_spend(),
            "payment_count": len(self.tracker.get_history()),
            "history": self.tracker.get_history(),
        }
