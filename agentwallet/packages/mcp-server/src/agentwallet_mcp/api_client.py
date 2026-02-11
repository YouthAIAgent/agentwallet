"""Lightweight async HTTP client for AgentWallet API.

Talks directly to the REST API — no SDK dependency needed.
This keeps the MCP server self-contained and deployable anywhere.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class AgentWalletClient:
    """Thin async wrapper around the AgentWallet REST API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("AGENTWALLET_API_KEY", "")
        self.base_url = (
            base_url or os.environ.get("AGENTWALLET_BASE_URL", "http://localhost:8000/v1")
        ).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=timeout,
        )

    async def close(self):
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        resp = await self._client.request(method, path, json=json, params=params)
        if resp.status_code >= 400:
            try:
                body = resp.json()
                detail = body.get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise AgentWalletAPIError(resp.status_code, detail)
        if resp.status_code == 204:
            return None
        return resp.json()

    async def get(self, path: str, params: dict | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict | None = None) -> Any:
        return await self._request("POST", path, json=json)

    async def patch(self, path: str, json: dict | None = None) -> Any:
        return await self._request("PATCH", path, json=json)

    async def delete(self, path: str) -> Any:
        return await self._request("DELETE", path)


class AgentWalletAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")
