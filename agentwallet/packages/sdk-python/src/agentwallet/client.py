"""Main AgentWallet SDK client -- Stripe-like interface."""

from __future__ import annotations

import httpx

from .exceptions import (
    AgentWalletAPIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .resources.agents import AgentsResource
from .resources.analytics import AnalyticsResource
from .resources.escrow import EscrowResource
from .resources.policies import PoliciesResource
from .resources.transactions import TransactionsResource
from .resources.wallets import WalletsResource

DEFAULT_BASE_URL = "http://localhost:8000/v1"

ERROR_MAP = {
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
}


class AgentWallet:
    """AgentWallet SDK client.

    Usage:
        async with AgentWallet(api_key="aw_live_...") as aw:
            agent = await aw.agents.create(name="trading-bot")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

        # Sub-resources
        self.agents = AgentsResource(self)
        self.wallets = WalletsResource(self)
        self.transactions = TransactionsResource(self)
        self.escrow = EscrowResource(self)
        self.analytics = AnalyticsResource(self)
        self.policies = PoliciesResource(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Make an authenticated API request."""
        resp = await self._client.request(method, path, json=json, params=params)

        if resp.status_code >= 400:
            body = {}
            try:
                body = resp.json()
            except Exception:
                pass
            message = body.get("error", body.get("detail", resp.text))
            error_cls = ERROR_MAP.get(resp.status_code, AgentWalletAPIError)
            raise error_cls(resp.status_code, message, body)

        if resp.status_code == 204:
            return {}
        return resp.json()

    async def get(self, path: str, params: dict | None = None) -> dict:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict | None = None) -> dict:
        return await self._request("POST", path, json=json)

    async def patch(self, path: str, json: dict | None = None) -> dict:
        return await self._request("PATCH", path, json=json)

    async def delete(self, path: str) -> dict:
        return await self._request("DELETE", path)
