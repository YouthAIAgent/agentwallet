"""Analytics sub-resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types import AnalyticsSummary

if TYPE_CHECKING:
    from ..client import AgentWallet


class AnalyticsResource:
    def __init__(self, client: AgentWallet):
        self._client = client

    async def summary(self, days: int = 30) -> AnalyticsSummary:
        data = await self._client.get("/analytics/summary", params={"days": days})
        return AnalyticsSummary(**data)

    async def daily(
        self, days: int = 30, agent_id: str | None = None
    ) -> list[dict]:
        params = {"days": days}
        if agent_id:
            params["agent_id"] = agent_id
        return await self._client.get("/analytics/daily", params=params)

    async def by_agent(self, days: int = 30) -> list[dict]:
        return await self._client.get("/analytics/agents", params={"days": days})
