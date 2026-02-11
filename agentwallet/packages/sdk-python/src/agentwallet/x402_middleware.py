"""x402 auto-payment middleware for httpx client."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from .x402_types import X402Response

if TYPE_CHECKING:
    from .client import AgentWallet

logger = logging.getLogger(__name__)


class X402AutoPay:
    """Middleware that wraps httpx client to auto-handle 402 responses.
    
    Usage:
        client = X402AutoPay(wallet_id="wallet_123", aw_client=aw, max_per_request=0.01)
        response = await client.get("https://api.weather.com/forecast")
        # If 402 → auto-pays → retries → returns data
    """

    def __init__(
        self,
        wallet_id: str,
        aw_client: AgentWallet,
        max_per_request: float = 0.10,
        **httpx_kwargs,
    ):
        """
        Initialize x402 auto-payment middleware.
        
        Args:
            wallet_id: AgentWallet wallet ID for payments
            aw_client: AgentWallet client instance
            max_per_request: Maximum USD per request (default: $0.10)
            **httpx_kwargs: Additional kwargs for httpx.AsyncClient
        """
        self.wallet_id = wallet_id
        self.aw_client = aw_client
        self.max_per_request = max_per_request
        self._client = httpx.AsyncClient(**httpx_kwargs)
        
        # Track payments for audit
        self._payments = []

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with automatic 402 payment handling."""
        x402_response = await self.aw_client.x402.pay_and_fetch(
            url=url,
            method=method,
            wallet_id=self.wallet_id,
            max_amount_usd=self.max_per_request,
            **kwargs,
        )
        
        # Log payment if one was made
        if x402_response.payment_required and x402_response.payment_proof:
            payment_log = {
                "url": url,
                "signature": x402_response.payment_proof.signature,
                "amount_usd": x402_response.cost_usd,
                "network": x402_response.payment_proof.network,
                "token": x402_response.payment_proof.token,
            }
            self._payments.append(payment_log)
            logger.info(f"x402 auto-payment: ${x402_response.cost_usd:.4f} to {url}")
        
        # Create httpx.Response object from x402 response
        response = httpx.Response(
            status_code=x402_response.status_code,
            headers={"content-type": "application/json"},
            content=str(x402_response.data).encode() if isinstance(x402_response.data, str) else str(x402_response.data).encode(),
        )
        
        return response

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request with auto-payment."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST request with auto-payment."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """PUT request with auto-payment."""
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """PATCH request with auto-payment."""
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """DELETE request with auto-payment."""
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs) -> httpx.Response:
        """HEAD request with auto-payment."""
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs) -> httpx.Response:
        """OPTIONS request with auto-payment."""
        return await self.request("OPTIONS", url, **kwargs)

    def get_payment_history(self) -> list[dict]:
        """Get audit trail of all payments made."""
        return self._payments.copy()

    def get_total_spent(self) -> float:
        """Get total USD spent through this client."""
        return sum(payment["amount_usd"] for payment in self._payments)

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()
        await self.aw_client.x402.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


class X402Budget:
    """Budget management for x402 payments."""
    
    def __init__(self, daily_limit: float = 1.0, per_request_limit: float = 0.10):
        self.daily_limit = daily_limit
        self.per_request_limit = per_request_limit
        self._daily_spent = 0.0
    
    def can_afford(self, amount_usd: float) -> bool:
        """Check if payment is within budget limits."""
        if amount_usd > self.per_request_limit:
            return False
        if self._daily_spent + amount_usd > self.daily_limit:
            return False
        return True
    
    def record_payment(self, amount_usd: float):
        """Record a payment against the budget."""
        self._daily_spent += amount_usd
    
    def reset_daily(self):
        """Reset daily spending counter."""
        self._daily_spent = 0.0
    
    def get_remaining_daily(self) -> float:
        """Get remaining daily budget."""
        return max(0.0, self.daily_limit - self._daily_spent)