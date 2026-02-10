"""Transactions sub-resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import ListResponse, Transaction

if TYPE_CHECKING:
    from ..client import AgentWallet


class TransactionsResource:
    def __init__(self, client: AgentWallet):
        self._client = client

    async def transfer_sol(
        self,
        from_wallet: str,
        to_address: str,
        amount_sol: float,
        memo: str | None = None,
        idempotency_key: str | None = None,
    ) -> Transaction:
        data = await self._client.post("/transactions/transfer-sol", json={
            "from_wallet_id": from_wallet,
            "to_address": to_address,
            "amount_sol": amount_sol,
            "memo": memo,
            "idempotency_key": idempotency_key,
        })
        return Transaction(**data)

    async def get(self, tx_id: str) -> Transaction:
        data = await self._client.get(f"/transactions/{tx_id}")
        return Transaction(**data)

    async def list(
        self,
        agent_id: str | None = None,
        wallet_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ListResponse:
        params = {"limit": limit, "offset": offset}
        if agent_id:
            params["agent_id"] = agent_id
        if wallet_id:
            params["wallet_id"] = wallet_id
        if status:
            params["status"] = status
        data = await self._client.get("/transactions", params=params)
        return ListResponse(
            data=[Transaction(**t) for t in data["data"]],
            total=data["total"],
        )

    async def batch_transfer(
        self, transfers: list[dict]
    ) -> list[Transaction]:
        data = await self._client.post("/transactions/batch-transfer", json={
            "transfers": transfers,
        })
        return [Transaction(**t) for t in data]
