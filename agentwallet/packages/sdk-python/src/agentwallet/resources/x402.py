"""x402 HTTP-native payment resource."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import httpx

from ..exceptions import AgentWalletAPIError
from ..x402_types import (
    X402PaymentInfo,
    X402PaymentProof,
    X402PaymentRequirement,
    X402Response,
)

if TYPE_CHECKING:
    from ..client import AgentWallet

logger = logging.getLogger(__name__)


class X402Resource:
    """Handle x402 HTTP-native payments automatically."""

    def __init__(self, client: AgentWallet):
        self.client = client
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def pay_and_fetch(
        self,
        url: str,
        method: str = "GET",
        wallet_id: str | None = None,
        max_amount_usd: float | None = None,
        **kwargs,
    ) -> X402Response:
        """Make HTTP request. If 402 received, auto-pay and retry.

        Flow:
        1. Make HTTP request to url
        2. If 200 OK → return response
        3. If 402 Payment Required → parse payment requirements
        4. Check if within policy/budget limits
        5. Execute payment via AgentWallet
        6. Retry request with payment proof header
        7. Return response

        Args:
            url: Target URL
            method: HTTP method (GET, POST, etc)
            wallet_id: AgentWallet wallet ID for payment
            max_amount_usd: Maximum USD amount willing to pay
            **kwargs: Additional arguments for httpx request
        """
        # Step 1: Initial request
        try:
            response = await self._http_client.request(method, url, **kwargs)

            # Step 2: If successful, return immediately
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                data = (
                    response.json()
                    if content_type.startswith("application/json")
                    else response.text
                )
                return X402Response(
                    status_code=200,
                    payment_required=False,
                    requirements=None,
                    data=data,
                    payment_proof=None,
                    cost_usd=0.0,
                )

            # Step 3: Handle 402 Payment Required
            if response.status_code == 402:
                payment_info = self._parse_402_response(response)
                requirement = self._select_best_payment_option(payment_info, max_amount_usd)

                if not requirement:
                    raise AgentWalletAPIError(
                        402,
                        "No acceptable payment method found",
                        payment_info.raw_body,
                        hint=(
                            "None of the provider's payment options fit your max_amount_usd -- "
                            "raise max_amount_usd or ask the provider for a cheaper option."
                        ),
                    )

                # Step 4: Check budget limits
                if max_amount_usd and requirement.amount and self._estimate_cost_usd(requirement) > max_amount_usd:
                    raise AgentWalletAPIError(
                        402,
                        f"Payment amount ${self._estimate_cost_usd(requirement):.4f} exceeds max ${max_amount_usd}",
                        {},
                        hint="Raise max_amount_usd, or pick a cheaper provider endpoint.",
                    )

                # Step 5: Execute payment
                payment_proof = await self._execute_payment(requirement, wallet_id)

                # Step 6: Retry with payment proof
                payment_headers = {
                    "X-Payment-Proof": json.dumps({
                        "network": payment_proof.network,
                        "token": payment_proof.token,
                        "signature": payment_proof.signature,
                        "amount": payment_proof.amount,
                    }),
                    **kwargs.get("headers", {}),
                }

                retry_kwargs = {**kwargs, "headers": payment_headers}
                retry_response = await self._http_client.request(method, url, **retry_kwargs)

                # Step 7: Return final response
                if retry_response.status_code == 200:
                    logger.info(f"x402 payment successful: {payment_proof.signature} for {url}")
                    content_type = retry_response.headers.get("content-type", "")
                    data = (
                        retry_response.json()
                        if content_type.startswith("application/json")
                        else retry_response.text
                    )
                    return X402Response(
                        status_code=200,
                        payment_required=True,
                        requirements=[requirement],
                        data=data,
                        payment_proof=payment_proof,
                        cost_usd=self._estimate_cost_usd(requirement),
                    )
                else:
                    raise AgentWalletAPIError(
                        retry_response.status_code,
                        f"Payment accepted but request failed: {retry_response.text}",
                        {},
                        hint=(
                            "Your payment already went through -- retry the request with the same "
                            "X-Payment-Proof header, or check the provider's error above."
                        ),
                    )

            # Other status codes
            raise AgentWalletAPIError(
                response.status_code,
                response.text,
                {},
                hint="The target endpoint returned an error -- check the URL and request method.",
            )

        except httpx.RequestError as e:
            raise AgentWalletAPIError(
                0,
                f"Network error: {str(e)}",
                {},
                hint="Check your network connection and that the target URL is reachable.",
            )

    async def discover(self, url: str) -> X402PaymentInfo | None:
        """Probe an endpoint to check if it supports x402 payments.
        Returns payment requirements without paying.
        """
        try:
            response = await self._http_client.request("OPTIONS", url)
            if response.status_code == 402:
                return self._parse_402_response(response)

            # Try a HEAD request
            response = await self._http_client.head(url)
            if response.status_code == 402:
                return self._parse_402_response(response)

            return None
        except Exception as e:
            logger.debug(f"Failed to discover x402 support for {url}: {e}")
            return None

    async def estimate(self, url: str, method: str = "GET") -> float:
        """Estimate cost of accessing an x402 endpoint without paying."""
        payment_info = await self.discover(url)
        if not payment_info:
            return 0.0

        requirement = self._select_best_payment_option(payment_info)
        if not requirement:
            return 0.0

        return self._estimate_cost_usd(requirement)

    def _parse_402_response(self, response: httpx.Response) -> X402PaymentInfo:
        """Parse 402 Payment Required response according to x402 spec."""
        try:
            body = response.json()
        except Exception:
            raise AgentWalletAPIError(
                402,
                "Invalid 402 response: not JSON",
                {},
                hint="This endpoint is not an x402 gateway -- check the URL.",
            )

        # Validate x402 format
        if "x402Version" not in body:
            raise AgentWalletAPIError(
                402,
                "Invalid x402 response: missing x402Version",
                body,
                hint="This endpoint returned 402 but is not x402-compliant -- check the URL.",
            )

        if "accepts" not in body:
            raise AgentWalletAPIError(
                402,
                "Invalid x402 response: missing accepts array",
                body,
                hint="The gateway did not list payment options -- contact the provider.",
            )

        return X402PaymentInfo(
            x402_version=body["x402Version"],
            description=body.get("description", "Payment required"),
            accepts=body["accepts"],
            raw_body=body,
        )

    def _select_best_payment_option(
        self,
        payment_info: X402PaymentInfo,
        max_amount_usd: float | None = None
    ) -> X402PaymentRequirement | None:
        """Select the best payment option from available methods.
        Prefers Solana USDC, then other Solana tokens, then other networks.
        """
        options = []

        for accept in payment_info.accepts:
            network = accept.get("network", "").lower()
            token = accept.get("token", "")
            amount = accept.get("amount", "0")
            pay_to = accept.get("payTo", accept.get("pay_to", ""))

            if not all([network, token, amount, pay_to]):
                continue

            requirement = X402PaymentRequirement(
                network=network,
                token=token,
                amount=str(amount),
                pay_to=pay_to,
                description=payment_info.description,
            )

            # Check budget limit
            if max_amount_usd:
                cost = self._estimate_cost_usd(requirement)
                if cost > max_amount_usd:
                    continue

            options.append((self._score_payment_option(requirement), requirement))

        if not options:
            return None

        # Return highest scoring option
        options.sort(reverse=True)
        return options[0][1]

    def _score_payment_option(self, requirement: X402PaymentRequirement) -> int:
        """Score payment options for preference (higher = better)."""
        score = 0

        # Prefer Solana
        if requirement.network.lower() == "solana":
            score += 100

        # Prefer USDC
        token_lower = requirement.token.lower()
        if "usdc" in token_lower:
            score += 50
        elif "usdt" in token_lower:
            score += 30
        elif "sol" in token_lower:
            score += 20

        # Prefer lower amounts (simple heuristic)
        try:
            amount = float(requirement.amount)
            if amount < 1000:  # Micro-payments
                score += 10
        except ValueError:
            pass

        return score

    def _estimate_cost_usd(self, requirement: X402PaymentRequirement) -> float:
        """Estimate USD cost of a payment requirement.
        This is a simple heuristic - in production you'd want real price feeds.
        """
        try:
            amount = float(requirement.amount)
            token_lower = requirement.token.lower()

            # Simple price estimates (in production, use real price feeds)
            if "usdc" in token_lower or "usdt" in token_lower:
                # Stablecoins - assume 1:1 with USD, handle decimals
                if requirement.network.lower() == "solana":
                    return amount / 1_000_000  # USDC on Solana has 6 decimals
                else:
                    return amount / 1_000_000_000_000_000_000  # Most EVM chains use 18 decimals
            elif "sol" in token_lower:
                # SOL - rough estimate $100 (use real price feed in production)
                return (amount / 1_000_000_000) * 100  # SOL has 9 decimals
            else:
                # Unknown token - assume small amount
                return amount / 1_000_000_000_000_000_000  # Default to 18 decimals
        except (ValueError, ZeroDivisionError):
            return 0.0

    async def _execute_payment(
        self,
        requirement: X402PaymentRequirement,
        wallet_id: str | None = None
    ) -> X402PaymentProof:
        """Execute payment via AgentWallet."""
        if not wallet_id:
            raise AgentWalletAPIError(
                400,
                "wallet_id required for x402 payments",
                {},
                hint="Pass a wallet_id -- create one first via aw.wallets.create().",
            )

        try:
            # Convert amount to lamports/smallest unit for AgentWallet
            amount_lamports = int(requirement.amount)

            # Determine token mint (None for SOL)
            token_mint = None
            if requirement.token.lower() != "sol":
                token_mint = requirement.token

            if token_mint is None:
                # Native SOL transfer
                tx_response = await self.client.transactions.transfer_sol(
                    from_wallet=wallet_id,
                    to_address=requirement.pay_to,
                    amount_sol=amount_lamports / 1e9,
                    memo=f"x402 payment: {requirement.description}",
                )
            else:
                # SPL token transfer via /tokens/transfer
                tx_response = await self.client.post("/tokens/transfer", json={
                    "from_wallet_id": wallet_id,
                    "to_address": requirement.pay_to,
                    "token_symbol": "USDC",
                    "amount": amount_lamports / 1e6,
                    "memo": f"x402 payment: {requirement.description}",
                })

            if isinstance(tx_response, dict):
                signature = tx_response.get("signature")
            else:
                signature = getattr(tx_response, "signature", None)
            if not signature:
                raise AgentWalletAPIError(
                    500,
                    "Payment failed: no signature returned",
                    tx_response,
                    hint="Check the wallet balance -- fund it (e.g. via the playground fund demo) and retry.",
                )

            return X402PaymentProof(
                network=requirement.network,
                token=requirement.token,
                signature=signature,
                amount=requirement.amount,
            )

        except Exception as e:
            logger.error(f"x402 payment execution failed: {e}")
            raise AgentWalletAPIError(
                500,
                f"Payment execution failed: {str(e)}",
                {},
                hint="Check the wallet balance and that the wallet is active, then retry.",
            )

    async def close(self):
        """Close the HTTP client."""
        await self._http_client.aclose()
