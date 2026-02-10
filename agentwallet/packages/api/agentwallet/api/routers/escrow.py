"""Escrow router -- create, release, refund, dispute."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.exceptions import EscrowStateError, NotFoundError
from ...services.escrow_service import EscrowService
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.escrow import (
    EscrowActionRequest,
    EscrowCreateRequest,
    EscrowListResponse,
    EscrowResponse,
)

router = APIRouter(prefix="/escrow", tags=["escrow"])


def _escrow_to_response(e) -> EscrowResponse:
    return EscrowResponse(
        id=e.id,
        org_id=e.org_id,
        funder_wallet_id=e.funder_wallet_id,
        recipient_address=e.recipient_address,
        arbiter_address=e.arbiter_address,
        escrow_address=e.escrow_address,
        amount_lamports=e.amount_lamports,
        token_mint=e.token_mint,
        status=e.status,
        conditions=e.conditions,
        fund_signature=e.fund_signature,
        release_signature=e.release_signature,
        refund_signature=e.refund_signature,
        dispute_reason=e.dispute_reason,
        expires_at=e.expires_at.isoformat() if e.expires_at else None,
        funded_at=e.funded_at.isoformat() if e.funded_at else None,
        completed_at=e.completed_at.isoformat() if e.completed_at else None,
        created_at=e.created_at.isoformat(),
    )


@router.post("", response_model=EscrowResponse, status_code=201)
async def create_escrow(
    req: EscrowCreateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = EscrowService(db)
    escrow = await svc.create_escrow(
        org_id=auth.org_id,
        funder_wallet_id=req.funder_wallet_id,
        recipient_address=req.recipient_address,
        amount_lamports=int(req.amount_sol * 1e9),
        token_mint=req.token_mint,
        arbiter_address=req.arbiter_address,
        conditions=req.conditions,
        expires_in_hours=req.expires_in_hours,
    )
    return _escrow_to_response(escrow)


@router.get("", response_model=EscrowListResponse)
async def list_escrows(
    request: Request,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = EscrowService(db)
    escrows, total = await svc.list_escrows(
        org_id=auth.org_id, status=status, limit=limit, offset=offset
    )
    return EscrowListResponse(
        data=[_escrow_to_response(e) for e in escrows],
        total=total,
    )


@router.get("/{escrow_id}", response_model=EscrowResponse)
async def get_escrow(
    escrow_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = EscrowService(db)
    escrow = await svc.get_escrow(escrow_id, auth.org_id)
    return _escrow_to_response(escrow)


@router.post("/{escrow_id}/action", response_model=EscrowResponse)
async def escrow_action(
    escrow_id: uuid.UUID,
    req: EscrowActionRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = EscrowService(db)

    try:
        if req.action == "release":
            escrow = await svc.release_escrow(escrow_id, auth.org_id)
        elif req.action == "refund":
            escrow = await svc.refund_escrow(escrow_id, auth.org_id)
        elif req.action == "dispute":
            escrow = await svc.dispute_escrow(escrow_id, auth.org_id, req.reason or "")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")
    except EscrowStateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _escrow_to_response(escrow)
