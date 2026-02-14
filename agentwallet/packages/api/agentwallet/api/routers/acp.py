"""ACP (Agent Commerce Protocol) router — 4-phase agent commerce."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.acp_service import AcpService
from ..middleware.auth import AuthContext, get_auth_context
from ..schemas.acp import (
    AcpDeliver,
    AcpEvaluate,
    AcpJobCreate,
    AcpJobListResponse,
    AcpJobResponse,
    AcpMemoCreate,
    AcpMemoListResponse,
    AcpMemoResponse,
    AcpNegotiate,
    ResourceOfferingCreate,
    ResourceOfferingListResponse,
    ResourceOfferingResponse,
)

router = APIRouter(prefix="/acp", tags=["Agent Commerce Protocol"])


def _job_to_response(job) -> AcpJobResponse:
    return AcpJobResponse(
        id=job.id,
        org_id=job.org_id,
        buyer_agent_id=job.buyer_agent_id,
        seller_agent_id=job.seller_agent_id,
        evaluator_agent_id=job.evaluator_agent_id,
        service_id=job.service_id,
        phase=job.phase,
        title=job.title,
        description=job.description,
        requirements=job.requirements or {},
        deliverables=job.deliverables or {},
        agreed_terms=job.agreed_terms,
        agreed_price_lamports=job.agreed_price_lamports,
        fund_transfer=job.fund_transfer,
        escrow_id=job.escrow_id,
        result_data=job.result_data,
        evaluation_notes=job.evaluation_notes,
        evaluation_approved=job.evaluation_approved,
        rating=job.rating,
        swarm_task_id=job.swarm_task_id,
        created_at=job.created_at,
        updated_at=job.updated_at,
        negotiated_at=job.negotiated_at,
        transacted_at=job.transacted_at,
        evaluated_at=job.evaluated_at,
        completed_at=job.completed_at,
    )


# ── Jobs ──


@router.post("/jobs", response_model=AcpJobResponse)
async def create_acp_job(
    body: AcpJobCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Create an ACP job (phase: request). Initiates the 4-phase commerce lifecycle."""
    svc = AcpService(db)
    job = await svc.create_job(
        org_id=auth.org_id,
        buyer_agent_id=body.buyer_agent_id,
        seller_agent_id=body.seller_agent_id,
        title=body.title,
        description=body.description,
        price_lamports=int(body.price_usdc * 1_000_000),
        service_id=body.service_id,
        evaluator_agent_id=body.evaluator_agent_id,
        requirements=body.requirements,
        deliverables=body.deliverables,
        fund_transfer=body.fund_transfer,
        principal_amount_lamports=int(body.principal_amount_usdc * 1_000_000) if body.principal_amount_usdc else None,
    )
    return _job_to_response(job)


@router.get("/jobs", response_model=AcpJobListResponse)
async def list_acp_jobs(
    agent_id: uuid.UUID | None = Query(None),
    phase: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """List ACP jobs for the org, optionally filtered by agent or phase."""
    svc = AcpService(db)
    jobs, total = await svc.list_jobs(auth.org_id, agent_id, phase, limit, offset)
    return AcpJobListResponse(
        jobs=[_job_to_response(j) for j in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/jobs/{job_id}", response_model=AcpJobResponse)
async def get_acp_job(
    job_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific ACP job with full lifecycle details."""
    svc = AcpService(db)
    job = await svc.get_job(job_id, auth.org_id)
    return _job_to_response(job)


@router.post("/jobs/{job_id}/negotiate", response_model=AcpJobResponse)
async def negotiate_job(
    job_id: uuid.UUID,
    body: AcpNegotiate,
    seller_agent_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Seller negotiates terms → advances to negotiation phase."""
    svc = AcpService(db)
    price = int(body.agreed_price_usdc * 1_000_000) if body.agreed_price_usdc else None
    job = await svc.negotiate(job_id, auth.org_id, seller_agent_id, body.agreed_terms, price)
    return _job_to_response(job)


@router.post("/jobs/{job_id}/fund", response_model=AcpJobResponse)
async def fund_job(
    job_id: uuid.UUID,
    buyer_agent_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Buyer funds escrow → advances to transaction phase."""
    svc = AcpService(db)
    job = await svc.start_transaction(job_id, auth.org_id, buyer_agent_id)
    return _job_to_response(job)


@router.post("/jobs/{job_id}/deliver", response_model=AcpJobResponse)
async def deliver_job(
    job_id: uuid.UUID,
    body: AcpDeliver,
    seller_agent_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Seller delivers results → advances to evaluation phase."""
    svc = AcpService(db)
    job = await svc.deliver(job_id, auth.org_id, seller_agent_id, body.result_data, body.notes)
    return _job_to_response(job)


@router.post("/jobs/{job_id}/evaluate", response_model=AcpJobResponse)
async def evaluate_job(
    job_id: uuid.UUID,
    body: AcpEvaluate,
    evaluator_agent_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Evaluator (or buyer) approves/rejects → completed or disputed."""
    svc = AcpService(db)
    job = await svc.evaluate(job_id, auth.org_id, evaluator_agent_id, body.approved, body.evaluation_notes, body.rating)
    return _job_to_response(job)


# ── Memos ──


@router.post("/jobs/{job_id}/memos", response_model=AcpMemoResponse)
async def send_memo(
    job_id: uuid.UUID,
    body: AcpMemoCreate,
    sender_agent_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Send a general memo on an ACP job (does not advance phase)."""
    svc = AcpService(db)
    memo = await svc.send_memo(job_id, auth.org_id, sender_agent_id, body.memo_type, body.content, body.signature)
    return AcpMemoResponse(
        id=memo.id, job_id=memo.job_id, sender_agent_id=memo.sender_agent_id,
        memo_type=memo.memo_type, content=memo.content, signature=memo.signature,
        tx_signature=memo.tx_signature, advances_phase=memo.advances_phase, created_at=memo.created_at,
    )


@router.get("/jobs/{job_id}/memos", response_model=AcpMemoListResponse)
async def list_memos(
    job_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """List all memos for an ACP job (audit trail)."""
    svc = AcpService(db)
    memos = await svc.list_memos(job_id, auth.org_id)
    return AcpMemoListResponse(
        memos=[AcpMemoResponse(
            id=m.id, job_id=m.job_id, sender_agent_id=m.sender_agent_id,
            memo_type=m.memo_type, content=m.content, signature=m.signature,
            tx_signature=m.tx_signature, advances_phase=m.advances_phase, created_at=m.created_at,
        ) for m in memos],
        total=len(memos),
    )


# ── Resource Offerings ──


@router.post("/offerings", response_model=ResourceOfferingResponse)
async def create_offering(
    body: ResourceOfferingCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Register a resource offering (lightweight data endpoint) for agent discovery."""
    svc = AcpService(db)
    offering = await svc.create_offering(
        auth.org_id, body.agent_id, body.name, body.description,
        body.endpoint_path, body.parameters, body.response_schema,
    )
    return ResourceOfferingResponse(
        id=offering.id, agent_id=offering.agent_id, org_id=offering.org_id,
        name=offering.name, description=offering.description, endpoint_path=offering.endpoint_path,
        parameters=offering.parameters, response_schema=offering.response_schema,
        is_active=offering.is_active, total_calls=offering.total_calls,
        avg_response_ms=offering.avg_response_ms, created_at=offering.created_at, updated_at=offering.updated_at,
    )


@router.get("/offerings", response_model=ResourceOfferingListResponse)
async def list_offerings(
    agent_id: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Discover resource offerings across agents."""
    svc = AcpService(db)
    offerings, total = await svc.list_offerings(auth.org_id, agent_id, limit, offset)
    return ResourceOfferingListResponse(
        offerings=[ResourceOfferingResponse(
            id=o.id, agent_id=o.agent_id, org_id=o.org_id,
            name=o.name, description=o.description, endpoint_path=o.endpoint_path,
            parameters=o.parameters, response_schema=o.response_schema,
            is_active=o.is_active, total_calls=o.total_calls,
            avg_response_ms=o.avg_response_ms, created_at=o.created_at, updated_at=o.updated_at,
        ) for o in offerings],
        total=total,
    )
