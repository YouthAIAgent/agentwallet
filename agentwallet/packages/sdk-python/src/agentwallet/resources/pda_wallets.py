"""PDA Wallets sub-resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import ListResponse, PDADeriveResult, PDATransferResult, PDAWallet, PDAWalletState

if TYPE_CHECKING:
    from ..client import AgentWallet


class PDAWalletsResource:
    def __init__(self, client: AgentWallet):
        self._client = client

    async def create(
        self,
        authority_wallet_id: str,
        agent_id_seed: str,
        spending_limit_per_tx: int,
        daily_limit: int,
        agent_id: str | None = None,
    ) -> PDAWallet:
        data = await self._client.post("/pda-wallets", json={
            "authority_wallet_id": authority_wallet_id,
            "agent_id_seed": agent_id_seed,
            "spending_limit_per_tx": spending_limit_per_tx,
            "daily_limit": daily_limit,
            "agent_id": agent_id,
        })
        return PDAWallet(**data)

    async def list(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> ListResponse:
        params = {"limit": limit, "offset": offset}
        data = await self._client.get("/pda-wallets", params=params)
        return ListResponse(
            data=[PDAWallet(**w) for w in data["data"]],
            total=data["total"],
        )

    async def get(self, pda_wallet_id: str) -> PDAWallet:
        data = await self._client.get(f"/pda-wallets/{pda_wallet_id}")
        return PDAWallet(**data)

    async def get_state(self, pda_wallet_id: str) -> PDAWalletState:
        data = await self._client.get(f"/pda-wallets/{pda_wallet_id}/state")
        return PDAWalletState(**data)

    async def transfer(
        self,
        pda_wallet_id: str,
        recipient: str,
        amount_lamports: int,
    ) -> PDATransferResult:
        data = await self._client.post(f"/pda-wallets/{pda_wallet_id}/transfer", json={
            "recipient": recipient,
            "amount_lamports": amount_lamports,
        })
        return PDATransferResult(**data)

    async def update_limits(
        self,
        pda_wallet_id: str,
        spending_limit_per_tx: int | None = None,
        daily_limit: int | None = None,
        is_active: bool | None = None,
    ) -> PDAWallet:
        payload = {}
        if spending_limit_per_tx is not None:
            payload["spending_limit_per_tx"] = spending_limit_per_tx
        if daily_limit is not None:
            payload["daily_limit"] = daily_limit
        if is_active is not None:
            payload["is_active"] = is_active
        data = await self._client.patch(f"/pda-wallets/{pda_wallet_id}/limits", json=payload)
        return PDAWallet(**data)

    async def derive_address(
        self,
        org_pubkey: str,
        agent_id_seed: str,
    ) -> PDADeriveResult:
        data = await self._client.post("/pda-wallets/derive", json={
            "org_pubkey": org_pubkey,
            "agent_id_seed": agent_id_seed,
        })
        return PDADeriveResult(**data)
