"""Public endpoint schemas — unauthenticated stats and feed."""

from datetime import datetime

from pydantic import BaseModel


class PublicStats(BaseModel):
    total_agents: int
    total_wallets: int
    total_transactions: int
    total_escrows: int
    total_acp_jobs: int
    total_swarms: int
    total_volume_sol: float
    api_endpoints: int = 88
    mcp_tools: int = 27
    tests_passing: int = 110
    router_groups: int = 16


class FeedItem(BaseModel):
    type: str
    action: str
    address: str
    amount: str | None = None
    timestamp: datetime


class PublicFeed(BaseModel):
    items: list[FeedItem]
    generated_at: datetime
