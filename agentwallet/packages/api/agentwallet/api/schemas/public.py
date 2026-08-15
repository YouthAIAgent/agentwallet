"""Public endpoint schemas — unauthenticated stats and feed."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


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


class PresenceRequest(BaseModel):
    """Anonymous heartbeat from a landing-page visitor."""

    visitor_id: Annotated[str, Field(min_length=8, max_length=64)]

    @field_validator("visitor_id")
    @classmethod
    def _safe_id(cls, v: str) -> str:
        v = v.strip()
        # Only allow typical id characters (uuid, v-<ts>-<rand>) to keep
        # Redis keys sane — never accept arbitrary user input verbatim.
        if not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError("visitor_id contains invalid characters")
        return v


class CountryCount(BaseModel):
    code: str
    count: int


class PresenceResponse(BaseModel):
    online: int
    countries: list[CountryCount] = []
