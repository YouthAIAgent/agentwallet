"""PDA Wallet router -- create, list, transfer, update limits for on-chain PDA wallets."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...services.pda_wallet_service import PDAWalletService
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.pda_wallets import (
    PDADeriveRequest,
    PDADeriveResponse,
    PDATransferRequest,
    PDATransferResponse,
    PDAUpdateLimitsRequest,
    PDAWalletCreateRequest,
    PDAWalletListResponse,
    PDAWalletResponse,
    PDAWalletStateResponse,
)

router = APIRouter(prefix="/pda-wallets", tags=["pda-wallets"])


def _wallet_response(pw) -> PDAWalletResponse:
    return PDAWalletResponse(
        id=pw.id,
        org_id=pw.org_id,
        pda_address=pw.pda_address,
        authority_wallet_id=pw.authority_wallet_id,
        agent_id=pw.agent_id,
        agent_id_seed=pw.agent_id_seed,
        spending_limit_per_tx=pw.spending_limit_per_tx,
        daily_limit=pw.daily_limit,
        bump=pw.bump,
        is_active=pw.is_active,
        tx_signature=pw.tx_signature,
        created_at=pw.created_at.isoformat(),
    )


@router.post("", response_model=PDAWalletResponse, status_code=201)
async def create_pda_wallet(
    req: PDAWalletCreateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Create a new PDA wallet on-chain with spending limits."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = PDAWalletService(db)
    pw = await svc.create_pda_wallet(
        org_id=auth.org_id,
        authority_wallet_id=req.authority_wallet_id,
        agent_id_seed=req.agent_id_seed,
        spending_limit_per_tx=req.spending_limit_per_tx,
        daily_limit=req.daily_limit,
        agent_id=req.agent_id,
    )
    return _wallet_response(pw)


@router.get("", response_model=PDAWalletListResponse)
async def list_pda_wallets(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """List PDA wallets for the authenticated organization."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = PDAWalletService(db)
    wallets, total = await svc.list_pda_wallets(
        org_id=auth.org_id, limit=limit, offset=offset,
    )
    return PDAWalletListResponse(
        data=[_wallet_response(w) for w in wallets],
        total=total,
    )


@router.get("/{wallet_id}", response_model=PDAWalletResponse)
async def get_pda_wallet(
    wallet_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get a PDA wallet by ID."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = PDAWalletService(db)
    pw = await svc.get_pda_wallet(wallet_id, auth.org_id)
    return _wallet_response(pw)


@router.get("/{wallet_id}/state", response_model=PDAWalletStateResponse)
async def get_pda_wallet_state(
    wallet_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Read on-chain state of a PDA wallet (live from Solana)."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = PDAWalletService(db)
    pw = await svc.get_pda_wallet(wallet_id, auth.org_id)
    state = await svc.get_pda_state(pw.pda_address)
    return PDAWalletStateResponse(**state)


@router.post("/{wallet_id}/transfer", response_model=PDATransferResponse)
async def transfer_from_pda(
    wallet_id: uuid.UUID,
    req: PDATransferRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Execute a transfer through the PDA wallet with on-chain limit enforcement."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = PDAWalletService(db)
    result = await svc.transfer_from_pda(
        pda_wallet_id=wallet_id,
        org_id=auth.org_id,
        recipient=req.recipient,
        amount_lamports=req.amount_lamports,
    )
    return PDATransferResponse(**result)


@router.patch("/{wallet_id}/limits", response_model=PDAWalletResponse)
async def update_pda_limits(
    wallet_id: uuid.UUID,
    req: PDAUpdateLimitsRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Update spending limits and active status of a PDA wallet on-chain."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = PDAWalletService(db)
    pw = await svc.update_pda_limits(
        pda_wallet_id=wallet_id,
        org_id=auth.org_id,
        spending_limit_per_tx=req.spending_limit_per_tx,
        daily_limit=req.daily_limit,
        is_active=req.is_active,
    )
    return _wallet_response(pw)


@router.post("/derive", response_model=PDADeriveResponse)
async def derive_pda_address(
    req: PDADeriveRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Derive a PDA address from org pubkey and agent ID seed (utility endpoint)."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    address, bump = PDAWalletService.derive_pda_address(req.org_pubkey, req.agent_id_seed)
    return PDADeriveResponse(pda_address=address, bump=bump)
