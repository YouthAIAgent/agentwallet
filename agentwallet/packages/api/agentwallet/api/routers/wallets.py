"""Wallet router -- create, list, balance queries."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.redis_client import CacheService, get_redis
from ...services.wallet_manager import WalletManager
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.wallets import (
    WalletBalanceResponse,
    WalletCreateRequest,
    WalletListResponse,
    WalletResponse,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("", response_model=WalletResponse, status_code=201)
async def create_wallet(
    req: WalletCreateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    mgr = WalletManager(db)
    wallet = await mgr.create_wallet(
        org_id=auth.org_id,
        org_tier=auth.org_tier,
        agent_id=req.agent_id,
        wallet_type=req.wallet_type,
        label=req.label,
    )
    return WalletResponse(
        id=wallet.id,
        org_id=wallet.org_id,
        agent_id=wallet.agent_id,
        address=wallet.address,
        wallet_type=wallet.wallet_type,
        label=wallet.label,
        is_active=wallet.is_active,
        created_at=wallet.created_at.isoformat(),
    )


@router.get("", response_model=WalletListResponse)
async def list_wallets(
    request: Request,
    agent_id: uuid.UUID | None = None,
    wallet_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    mgr = WalletManager(db)
    wallets, total = await mgr.list_wallets(
        org_id=auth.org_id,
        agent_id=agent_id,
        wallet_type=wallet_type,
        limit=limit,
        offset=offset,
    )
    return WalletListResponse(
        data=[
            WalletResponse(
                id=w.id,
                org_id=w.org_id,
                agent_id=w.agent_id,
                address=w.address,
                wallet_type=w.wallet_type,
                label=w.label,
                is_active=w.is_active,
                created_at=w.created_at.isoformat(),
            )
            for w in wallets
        ],
        total=total,
    )


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    mgr = WalletManager(db)
    wallet = await mgr.get_wallet(wallet_id, auth.org_id)
    return WalletResponse(
        id=wallet.id,
        org_id=wallet.org_id,
        agent_id=wallet.agent_id,
        address=wallet.address,
        wallet_type=wallet.wallet_type,
        label=wallet.label,
        is_active=wallet.is_active,
        created_at=wallet.created_at.isoformat(),
    )


@router.get("/{wallet_id}/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    wallet_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    r = await get_redis()
    mgr = WalletManager(db, cache=CacheService(r))
    result = await mgr.get_balance(wallet_id, auth.org_id)
    return WalletBalanceResponse(**result)
