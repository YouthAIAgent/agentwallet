"""Analytics request/response schemas."""

import uuid

from pydantic import BaseModel


class AnalyticsSummaryResponse(BaseModel):
    total_spend_lamports: int
    total_fees_lamports: int
    tx_count: int
    failed_tx_count: int
    active_agents: int
    unique_destinations: int
    period_start: str
    period_end: str


class DailyMetricResponse(BaseModel):
    date: str
    tx_count: int
    total_spend_lamports: int
    total_fees_lamports: int
    unique_destinations: int
    failed_tx_count: int


class AgentAnalyticsResponse(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    tx_count: int
    total_spend_lamports: int
    total_fees_lamports: int
    top_destinations: list[dict]


class SpendingReportResponse(BaseModel):
    data: list[dict]
    group_by: str
    period_start: str
    period_end: str
    total_spend_lamports: int
