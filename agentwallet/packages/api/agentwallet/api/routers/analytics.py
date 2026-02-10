"""Analytics router -- dashboard metrics, spending reports."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.analytics_engine import AnalyticsEngine
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.analytics import AnalyticsSummaryResponse, DailyMetricResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_summary(
    request: Request,
    days: int = 30,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    engine = AnalyticsEngine(db)
    return await engine.get_summary(auth.org_id, days=days)


@router.get("/daily", response_model=list[DailyMetricResponse])
async def get_daily_metrics(
    request: Request,
    days: int = 30,
    agent_id: uuid.UUID | None = None,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    engine = AnalyticsEngine(db)
    return await engine.get_daily_metrics(auth.org_id, days=days, agent_id=agent_id)


@router.get("/agents")
async def get_agent_analytics(
    request: Request,
    days: int = 30,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    engine = AnalyticsEngine(db)
    return await engine.get_agent_analytics(auth.org_id, days=days)
