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
from .resources.acp import AcpResource
from .resources.agents import AgentsResource
from .resources.analytics import AnalyticsResource
from .resources.escrow import EscrowResource
from .resources.pda_wallets import PDAWalletsResource
from .resources.policies import PoliciesResource
from .resources.swarms import SwarmsResource
from .resources.transactions import TransactionsResource
from .resources.wallets import WalletsResource
from .resources.x402 import X402Resource

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
        self.pda_wallets = PDAWalletsResource(self)
        self.x402 = X402Resource(self)
        self.acp = AcpResource(self)
        self.swarms = SwarmsResource(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        await self._client.aclose()
        await self.x402.close()

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Make an authenticated API request."""
        try:
            resp = await self._client.request(method, path, json=json, params=params)
        except httpx.RequestError as e:
            raise AgentWalletAPIError(
                0,
                f"Network error: {e}",
                hint=(
                    f"Could not reach {self.base_url}{path} -- check that the API is running "
                    "and the base_url/api key are correct."
                ),
            )

        if resp.status_code >= 400:
            body = {}
            try:
                body = resp.json()
            except Exception:
                pass
            message = body.get("error", body.get("detail", resp.text))
            error_cls = ERROR_MAP.get(resp.status_code, AgentWalletAPIError)

            # Prefer an explicit hint from the server body; the API already embeds
            # action hints in many detail messages, so only fall back when missing.
            hint = body.get("hint") if isinstance(body, dict) else None
            msg_str = message if isinstance(message, str) else str(message)
            if hint is None and ("--" in msg_str or "—" in msg_str):
                hint = ""  # message already embeds the next step -- don't append
            raise error_cls(resp.status_code, message, body, hint=hint)

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
