"""Agents sub-resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import Agent, ListResponse

if TYPE_CHECKING:
    from ..client import AgentWallet


class AgentsResource:
    def __init__(self, client: AgentWallet):
        self._client = client

    async def create(
        self,
        name: str,
        description: str | None = None,
        capabilities: list[str] | None = None,
        is_public: bool = False,
        metadata: dict | None = None,
    ) -> Agent:
        data = await self._client.post("/agents", json={
            "name": name,
            "description": description,
            "capabilities": capabilities or [],
            "is_public": is_public,
            "metadata": metadata or {},
        })
        return Agent(**data)

    async def get(self, agent_id: str) -> Agent:
        data = await self._client.get(f"/agents/{agent_id}")
        return Agent(**data)

    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ListResponse:
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        data = await self._client.get("/agents", params=params)
        return ListResponse(
            data=[Agent(**a) for a in data["data"]],
            total=data["total"],
        )

    async def update(self, agent_id: str, **kwargs) -> Agent:
        data = await self._client.patch(f"/agents/{agent_id}", json=kwargs)
        return Agent(**data)
