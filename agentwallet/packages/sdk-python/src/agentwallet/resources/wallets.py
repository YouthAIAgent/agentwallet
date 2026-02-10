"""Wallets sub-resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import ListResponse, Wallet, WalletBalance

if TYPE_CHECKING:
    from ..client import AgentWallet


class WalletsResource:
    def __init__(self, client: AgentWallet):
        self._client = client

    async def create(
        self,
        agent_id: str | None = None,
        wallet_type: str = "agent",
        label: str | None = None,
    ) -> Wallet:
        data = await self._client.post("/wallets", json={
            "agent_id": agent_id,
            "wallet_type": wallet_type,
            "label": label,
        })
        return Wallet(**data)

    async def get(self, wallet_id: str) -> Wallet:
        data = await self._client.get(f"/wallets/{wallet_id}")
        return Wallet(**data)

    async def list(
        self,
        agent_id: str | None = None,
        wallet_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ListResponse:
        params = {"limit": limit, "offset": offset}
        if agent_id:
            params["agent_id"] = agent_id
        if wallet_type:
            params["wallet_type"] = wallet_type
        data = await self._client.get("/wallets", params=params)
        return ListResponse(
            data=[Wallet(**w) for w in data["data"]],
            total=data["total"],
        )

    async def get_balance(self, wallet_id: str) -> WalletBalance:
        data = await self._client.get(f"/wallets/{wallet_id}/balance")
        return WalletBalance(**data)
