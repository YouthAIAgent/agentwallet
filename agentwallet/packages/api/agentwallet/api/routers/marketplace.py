"""Marketplace router -- agent-to-agent service discovery, jobs, reputation."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.exceptions import ConflictError, NotFoundError, ValidationError
from ...services.marketplace_service import MarketplaceService
from ...services.reputation_service import ReputationService
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.marketplace import (
    AgentReputationResponse,
    JobAccept,
    JobCancel,
    JobComplete,
    JobCreate,
    JobMessageCreate,
    JobMessageResponse,
    JobRate,
    JobResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    MarketplaceStatsResponse,
    ServiceAnalyticsResponse,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


def _service_to_response(s) -> ServiceResponse:
    return ServiceResponse(
        id=s.id,
        agent_id=s.agent_id,
        name=s.name,
        description=s.description,
        price_usdc=s.price_lamports / 1_000_000,
        token_symbol=s.token_symbol,
        capabilities=s.capabilities or [],
        is_active=s.is_active,
        estimated_duration_hours=s.estimated_duration_hours,
        max_concurrent_jobs=s.max_concurrent_jobs,
        requirements=s.requirements or {},
        delivery_format=s.delivery_format,
        total_jobs=s.total_jobs,
        completed_jobs=s.completed_jobs,
        avg_rating=s.avg_rating,
        success_rate=s.success_rate,
        created_at=s.created_at,
        updated_at=s.updated_at,
        agent_name=getattr(s, "agent", None) and s.agent.name,
        agent_reputation_score=None,
    )


def _job_to_response(j) -> JobResponse:
    return JobResponse(
        id=j.id,
        service_id=j.service_id,
        buyer_agent_id=j.buyer_agent_id,
        seller_agent_id=j.seller_agent_id,
        escrow_id=j.escrow_id,
        status=j.status,
        input_data=j.input_data or {},
        result_data=j.result_data,
        buyer_notes=j.buyer_notes,
        seller_notes=j.seller_notes,
        rating=j.rating,
        review=j.review,
        seller_response=j.seller_response,
        created_at=j.created_at,
        started_at=j.started_at,
        completed_at=j.completed_at,
        deadline=j.deadline,
        service_name=getattr(j, "service", None) and j.service.name,
        service_price_usdc=getattr(j, "service", None) and j.service.price_lamports / 1_000_000,
        buyer_agent_name=getattr(j, "buyer_agent", None) and j.buyer_agent.name,
        seller_agent_name=getattr(j, "seller_agent", None) and j.seller_agent.name,
    )


def _message_to_response(m) -> JobMessageResponse:
    return JobMessageResponse(
        id=m.id,
        job_id=m.job_id,
        sender_agent_id=m.sender_agent_id,
        message_type=m.message_type,
        content=m.content,
        attachments=m.attachments or {},
        is_system_message=m.is_system_message,
        read_at=m.read_at,
        created_at=m.created_at,
        sender_agent_name=getattr(m, "sender", None) and m.sender.name,
    )


# ── Services ──────────────────────────────────────────────


@router.post("/services", response_model=ServiceResponse, status_code=201)
async def register_service(
    req: ServiceCreate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    try:
        service = await svc.register_service(
            agent_id=req.agent_id,
            service_name=req.name,
            description=req.description,
            price_usdc=req.price_usdc,
            capabilities=req.capabilities,
            estimated_duration_hours=req.estimated_duration_hours,
            max_concurrent_jobs=req.max_concurrent_jobs,
            requirements=req.requirements,
            delivery_format=req.delivery_format,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _service_to_response(service)


@router.get("/services", response_model=list[ServiceResponse])
async def discover_services(
    request: Request,
    query: Optional[str] = None,
    capability: Optional[str] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    agent_id: Optional[uuid.UUID] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    services = await svc.discover_services(
        query=query,
        capability=capability,
        max_price=max_price,
        min_rating=min_rating,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )
    return [_service_to_response(s) for s in services]


@router.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    from sqlalchemy import select
    from ...models.marketplace import Service

    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return _service_to_response(service)


@router.patch("/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: uuid.UUID,
    req: ServiceUpdate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    from sqlalchemy import select
    from ...models.marketplace import Service

    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    update_data = req.model_dump(exclude_unset=True)
    if "price_usdc" in update_data:
        service.price_lamports = int(update_data.pop("price_usdc") * 1_000_000)
    for field, value in update_data.items():
        setattr(service, field, value)
    await db.flush()
    await db.refresh(service)
    return _service_to_response(service)


@router.get("/services/{service_id}/analytics", response_model=ServiceAnalyticsResponse)
async def service_analytics(
    service_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    try:
        data = await svc.get_service_analytics(service_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ServiceAnalyticsResponse(**data)


# ── Jobs ──────────────────────────────────────────────────


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    req: JobCreate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    try:
        job = await svc.hire_agent(
            buyer_agent_id=req.buyer_agent_id,
            seller_agent_id=req.seller_agent_id,
            service_id=req.service_id,
            wallet_id=req.wallet_id,
            input_data=req.input_data,
            buyer_notes=req.buyer_notes,
            deadline_hours=req.deadline_hours,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _job_to_response(job)


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    request: Request,
    agent_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    as_buyer: Optional[bool] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    if not agent_id:
        agent_id = getattr(auth, "agent_id", None)
    jobs = await svc.get_agent_jobs(
        agent_id=agent_id,
        status=status,
        as_buyer=as_buyer,
        limit=limit,
        offset=offset,
    )
    return [_job_to_response(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    from ...models.marketplace import Job

    result = await db.execute(
        select(Job)
        .options(joinedload(Job.service), joinedload(Job.buyer_agent), joinedload(Job.seller_agent))
        .where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.post("/jobs/{job_id}/accept", response_model=JobResponse)
async def accept_job(
    job_id: uuid.UUID,
    req: JobAccept,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    try:
        job = await svc.accept_job(job_id, req.seller_agent_id, req.seller_notes)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _job_to_response(job)


@router.post("/jobs/{job_id}/complete", response_model=JobResponse)
async def complete_job(
    job_id: uuid.UUID,
    req: JobComplete,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    try:
        job = await svc.complete_job(job_id, auth.agent_id, req.result_data, req.completion_notes)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _job_to_response(job)


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: uuid.UUID,
    req: JobCancel,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    try:
        job = await svc.cancel_job(job_id, auth.agent_id, req.reason)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _job_to_response(job)


@router.post("/jobs/{job_id}/rate", response_model=JobResponse)
async def rate_job(
    job_id: uuid.UUID,
    req: JobRate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    try:
        job = await svc.rate_agent(job_id, auth.agent_id, req.rating, req.review)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _job_to_response(job)


# ── Messages ──────────────────────────────────────────────


@router.get("/jobs/{job_id}/messages", response_model=list[JobMessageResponse])
async def get_messages(
    job_id: uuid.UUID,
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    try:
        messages = await svc.get_job_messages(job_id, auth.agent_id, limit, offset)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [_message_to_response(m) for m in messages]


@router.post("/jobs/{job_id}/messages", response_model=JobMessageResponse, status_code=201)
async def send_message(
    job_id: uuid.UUID,
    req: JobMessageCreate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = MarketplaceService(db)
    try:
        message = await svc.send_job_message(job_id, auth.agent_id, req.content, req.message_type, req.attachments)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _message_to_response(message)


# ── Reputation & Leaderboard ─────────────────────────────


@router.get("/reputation/{agent_id}", response_model=AgentReputationResponse)
async def get_reputation(
    agent_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ReputationService(db)
    try:
        reputation = await svc.get_or_create_reputation(agent_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return AgentReputationResponse(
        agent_id=reputation.agent_id,
        score=reputation.score,
        total_jobs=reputation.total_jobs,
        completed_jobs=reputation.completed_jobs,
        cancelled_jobs=reputation.cancelled_jobs,
        disputed_jobs=reputation.disputed_jobs,
        avg_rating=reputation.avg_rating,
        rating_count=reputation.rating_count,
        five_star_count=reputation.five_star_count,
        four_star_count=reputation.four_star_count,
        three_star_count=reputation.three_star_count,
        two_star_count=reputation.two_star_count,
        one_star_count=reputation.one_star_count,
        total_volume_usdc=reputation.total_volume_lamports / 1_000_000,
        total_earnings_usdc=reputation.total_earnings_lamports / 1_000_000,
        total_spent_usdc=reputation.total_spent_lamports / 1_000_000,
        avg_completion_time_hours=reputation.avg_completion_time_hours,
        on_time_delivery_rate=reputation.on_time_delivery_rate,
        response_time_hours=reputation.response_time_hours,
        reliability_score=reputation.reliability_score,
        quality_score=reputation.quality_score,
        communication_score=reputation.communication_score,
        first_job_at=reputation.first_job_at,
        last_job_at=reputation.last_job_at,
        updated_at=reputation.updated_at,
    )


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    request: Request,
    category: Optional[str] = None,
    min_jobs: int = Query(5, ge=0),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ReputationService(db)
    results = await svc.get_leaderboard(limit=limit, category=category, min_jobs=min_jobs)

    entries = []
    for agent, reputation in results:
        entries.append(
            LeaderboardEntry(
                agent_id=agent.id,
                agent_name=agent.name,
                reputation_score=reputation.score,
                total_jobs=reputation.total_jobs,
                avg_rating=reputation.avg_rating,
                total_volume_usdc=reputation.total_volume_lamports / 1_000_000,
                capabilities=agent.capabilities or [],
                active_services=0,
            )
        )

    return LeaderboardResponse(
        entries=entries,
        total_agents=len(entries),
        category=category,
        min_jobs_filter=min_jobs,
    )


@router.get("/stats", response_model=MarketplaceStatsResponse)
async def marketplace_stats(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    from sqlalchemy import func, select
    from ...models.marketplace import Job, Service

    # Aggregate stats
    svc_result = await db.execute(
        select(
            func.count(Service.id).label("total"),
            func.count(Service.id).filter(Service.is_active == True).label("active"),
        )
    )
    svc_stats = svc_result.first()

    job_result = await db.execute(
        select(
            func.count(Job.id).label("total"),
            func.count(Job.id).filter(Job.status == "completed").label("completed"),
            func.sum(Service.price_lamports).label("total_volume"),
        )
        .select_from(Job)
        .join(Service)
    )
    job_stats = job_result.first()

    total_jobs = job_stats.total or 0
    total_volume = (job_stats.total_volume or 0) / 1_000_000

    return MarketplaceStatsResponse(
        total_services=svc_stats.total or 0,
        active_services=svc_stats.active or 0,
        total_jobs=total_jobs,
        completed_jobs=job_stats.completed or 0,
        total_volume_usdc=total_volume,
        average_job_value_usdc=total_volume / total_jobs if total_jobs else 0,
        top_categories=[],
        recent_activity=[],
    )
