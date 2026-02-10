"""Escrow sub-resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import Escrow, ListResponse

if TYPE_CHECKING:
    from ..client import AgentWallet


class EscrowResource:
    def __init__(self, client: AgentWallet):
        self._client = client

    async def create(
        self,
        funder_wallet: str,
        recipient_address: str,
        amount_sol: float,
        token_mint: str | None = None,
        arbiter_address: str | None = None,
        conditions: dict | None = None,
        expires_in_hours: int = 24,
    ) -> Escrow:
        data = await self._client.post("/escrow", json={
            "funder_wallet_id": funder_wallet,
            "recipient_address": recipient_address,
            "amount_sol": amount_sol,
            "token_mint": token_mint,
            "arbiter_address": arbiter_address,
            "conditions": conditions or {},
            "expires_in_hours": expires_in_hours,
        })
        return Escrow(**data)

    async def get(self, escrow_id: str) -> Escrow:
        data = await self._client.get(f"/escrow/{escrow_id}")
        return Escrow(**data)

    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ListResponse:
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        data = await self._client.get("/escrow", params=params)
        return ListResponse(
            data=[Escrow(**e) for e in data["data"]],
            total=data["total"],
        )

    async def release(self, escrow_id: str) -> Escrow:
        data = await self._client.post(f"/escrow/{escrow_id}/action", json={
            "action": "release",
        })
        return Escrow(**data)

    async def refund(self, escrow_id: str) -> Escrow:
        data = await self._client.post(f"/escrow/{escrow_id}/action", json={
            "action": "refund",
        })
        return Escrow(**data)

    async def dispute(self, escrow_id: str, reason: str) -> Escrow:
        data = await self._client.post(f"/escrow/{escrow_id}/action", json={
            "action": "dispute",
            "reason": reason,
        })
        return Escrow(**data)
