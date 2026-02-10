"""Policies sub-resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import ListResponse, Policy

if TYPE_CHECKING:
    from ..client import AgentWallet


class PoliciesResource:
    def __init__(self, client: AgentWallet):
        self._client = client

    async def create(
        self,
        name: str,
        rules: dict,
        scope_type: str = "org",
        scope_id: str | None = None,
        priority: int = 100,
    ) -> Policy:
        data = await self._client.post("/policies", json={
            "name": name,
            "rules": rules,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "priority": priority,
        })
        return Policy(**data)

    async def get(self, policy_id: str) -> Policy:
        data = await self._client.get(f"/policies/{policy_id}")
        return Policy(**data)

    async def list(self, limit: int = 50, offset: int = 0) -> ListResponse:
        data = await self._client.get("/policies", params={"limit": limit, "offset": offset})
        return ListResponse(
            data=[Policy(**p) for p in data["data"]],
            total=data["total"],
        )

    async def update(self, policy_id: str, **kwargs) -> Policy:
        data = await self._client.patch(f"/policies/{policy_id}", json=kwargs)
        return Policy(**data)

    async def delete(self, policy_id: str) -> None:
        await self._client.delete(f"/policies/{policy_id}")
