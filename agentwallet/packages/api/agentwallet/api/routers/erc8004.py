"""ERC-8004 router -- identity, reputation, feedback, EVM wallets."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.exceptions import ERC8004Error, NotFoundError, ValidationError
from ...services.erc8004_service import ERC8004Service
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.erc8004 import (
    BridgeEscrowFeedbackRequest,
    EVMWalletResponse,
    FeedbackListResponse,
    FeedbackResponse,
    IdentityResponse,
    RegisterIdentityRequest,
    ReputationResponse,
    SubmitFeedbackRequest,
)

router = APIRouter(prefix="/erc8004", tags=["erc8004"])


def _identity_to_response(i) -> IdentityResponse:
    return IdentityResponse(
        id=i.id,
        agent_id=i.agent_id,
        token_id=i.token_id,
        evm_address=i.evm_address,
        chain_id=i.chain_id,
        metadata_uri=i.metadata_uri,
        status=i.status,
        tx_hash=i.tx_hash,
        created_at=i.created_at.isoformat(),
    )


def _feedback_to_response(f) -> FeedbackResponse:
    return FeedbackResponse(
        id=f.id,
        from_agent_id=f.from_agent_id,
        to_agent_id=f.to_agent_id,
        rating=f.rating,
        comment=f.comment,
        task_reference=f.task_reference,
        tx_hash=f.tx_hash,
        status=f.status,
        created_at=f.created_at.isoformat(),
    )


def _evm_wallet_to_response(w) -> EVMWalletResponse:
    return EVMWalletResponse(
        id=w.id,
        agent_id=w.agent_id,
        address=w.address,
        chain_id=w.chain_id,
        label=w.label,
        created_at=w.created_at.isoformat(),
    )


# ------------------------------------------------------------------
# Identity
# ------------------------------------------------------------------


@router.post("/identity/{agent_id}", response_model=IdentityResponse, status_code=201)
async def register_identity(
    agent_id: uuid.UUID,
    req: RegisterIdentityRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Register an agent on the ERC-8004 Identity Registry (Base L2)."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ERC8004Service(db)
    try:
        identity = await svc.register_identity(agent_id, auth.org_id, req.metadata_uri)
    except ERC8004Error as e:
        raise HTTPException(status_code=409, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _identity_to_response(identity)


@router.get("/identity/{agent_id}", response_model=IdentityResponse)
async def get_identity(
    agent_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get an agent's ERC-8004 identity."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ERC8004Service(db)
    try:
        identity = await svc.get_identity(agent_id, auth.org_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _identity_to_response(identity)


# ------------------------------------------------------------------
# Feedback
# ------------------------------------------------------------------


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    req: SubmitFeedbackRequest,
    request: Request,
    from_agent_id: uuid.UUID = Query(..., description="The agent submitting feedback"),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Submit on-chain feedback for an agent."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ERC8004Service(db)
    try:
        feedback = await svc.submit_feedback(
            from_agent_id=from_agent_id,
            to_agent_id=req.to_agent_id,
            org_id=auth.org_id,
            rating=req.rating,
            comment=req.comment,
            task_reference=req.task_reference,
        )
    except (ERC8004Error, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _feedback_to_response(feedback)


@router.get("/feedback/{agent_id}", response_model=FeedbackListResponse)
async def list_feedback(
    agent_id: uuid.UUID,
    request: Request,
    direction: str = Query("received", pattern="^(received|given)$"),
    limit: int = Query(50, le=100),
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """List feedback given or received by an agent."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ERC8004Service(db)
    try:
        items, total = await svc.list_feedback(agent_id, auth.org_id, direction=direction, limit=limit, offset=offset)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FeedbackListResponse(
        data=[_feedback_to_response(f) for f in items],
        total=total,
    )


# ------------------------------------------------------------------
# Reputation
# ------------------------------------------------------------------


@router.get("/reputation/{agent_id}", response_model=ReputationResponse)
async def get_reputation(
    agent_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get an agent's on-chain reputation score."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ERC8004Service(db)
    try:
        result = await svc.get_reputation(agent_id, auth.org_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ReputationResponse(**result)


@router.post("/reputation/{agent_id}/sync", response_model=ReputationResponse)
async def sync_reputation(
    agent_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Sync an agent's reputation from on-chain to local DB."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ERC8004Service(db)
    try:
        result = await svc.sync_reputation(agent_id, auth.org_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ReputationResponse(**result)


# ------------------------------------------------------------------
# Escrow Bridge
# ------------------------------------------------------------------


@router.post("/escrow/{escrow_id}/feedback", response_model=FeedbackResponse, status_code=201)
async def bridge_escrow_feedback(
    escrow_id: uuid.UUID,
    req: BridgeEscrowFeedbackRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback after an escrow is released, linking it to the escrow."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ERC8004Service(db)
    try:
        feedback = await svc.bridge_escrow_feedback(escrow_id, auth.org_id, req.rating, req.comment)
    except (ERC8004Error, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not feedback:
        raise HTTPException(status_code=400, detail="Could not create feedback for this escrow")
    return _feedback_to_response(feedback)


# ------------------------------------------------------------------
# EVM Wallet
# ------------------------------------------------------------------


@router.get("/evm-wallet/{agent_id}", response_model=EVMWalletResponse)
async def get_evm_wallet(
    agent_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get an agent's EVM wallet."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ERC8004Service(db)
    try:
        wallet = await svc.get_evm_wallet(agent_id, auth.org_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _evm_wallet_to_response(wallet)


@router.post("/evm-wallet/{agent_id}", response_model=EVMWalletResponse, status_code=201)
async def create_evm_wallet(
    agent_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Create an EVM wallet for an agent (Base L2)."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = ERC8004Service(db)
    try:
        wallet = await svc.create_evm_wallet(agent_id, auth.org_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _evm_wallet_to_response(wallet)
