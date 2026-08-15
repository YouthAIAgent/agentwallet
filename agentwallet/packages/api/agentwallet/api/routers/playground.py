"""Devnet Playground — one-click demos that run REAL on-chain transactions.

Every endpoint signs and submits an actual Solana devnet transaction, so
each result carries a signature linkable on the devnet explorer:

    GET  /playground          -> org wallet + balance + platform address
    POST /playground/fund     -> platform wallet -> org wallet (0.05 SOL)
    POST /playground/escrow   -> create + fund an escrow (0.02 SOL)
    POST /playground/escrow/{escrow_id}/release -> release escrow on-chain
    POST /playground/transfer -> org wallet -> platform (0.01 SOL)
"""

import time
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core import solana
from ...core.config import get_settings
from ...core.database import get_db
from ...models.wallet import Wallet
from ...services.escrow_service import EscrowService
from ...services.wallet_manager import WalletManager
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit

router = APIRouter(prefix="/playground", tags=["playground"])

FUND_SOL = 0.05
ESCROW_SOL = 0.02
TRANSFER_SOL = 0.01
FUND_COOLDOWN_SECONDS = 60

# per-org cooldown so nobody can drain the funded platform wallet
_fund_cooldown: dict[str, float] = {}

_platform_address_cache: str | None = None


def _platform_address() -> str:
    global _platform_address_cache
    if _platform_address_cache:
        return _platform_address_cache
    settings = get_settings()
    if settings.platform_wallet_address:
        _platform_address_cache = settings.platform_wallet_address
    else:
        _platform_address_cache = str(solana.load_platform_keypair().pubkey())
    return _platform_address_cache


def _explorer(signature: str) -> str:
    return f"https://explorer.solana.com/tx/{signature}?cluster=devnet"


async def _ensure_wallet(db: AsyncSession, auth: AuthContext) -> Wallet:
    wallet = await db.scalar(
        select(Wallet)
        .where(Wallet.org_id == auth.org_id)
        .order_by(Wallet.created_at.asc())
        .limit(1)
    )
    if wallet is None:
        mgr = WalletManager(db)
        wallet = await mgr.create_wallet(
            org_id=auth.org_id,
            org_tier=auth.org_tier,
            wallet_type="treasury",
            label="devnet-playground",
        )
    return wallet


class PlaygroundStatusResponse(BaseModel):
    wallet_id: str | None
    wallet_address: str | None
    balance_sol: float
    platform_address: str
    network: str


@router.get("", response_model=PlaygroundStatusResponse)
async def playground_status(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    wallet = await _ensure_wallet(db, auth)
    balance = 0.0
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            lamports = await solana.get_balance(client, wallet.address)
            balance = lamports / 1e9
    except Exception:
        pass
    return PlaygroundStatusResponse(
        wallet_id=str(wallet.id),
        wallet_address=wallet.address,
        balance_sol=balance,
        platform_address=_platform_address(),
        network=get_settings().solana_network,
    )


class FundResponse(BaseModel):
    wallet_id: str
    wallet_address: str
    amount_sol: float
    signature: str
    confirmed: bool
    explorer_url: str


@router.post("/fund", response_model=FundResponse, status_code=201)
async def playground_fund(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    org_key = str(auth.org_id)
    now = time.monotonic()
    if now - _fund_cooldown.get(org_key, 0) < FUND_COOLDOWN_SECONDS:
        raise HTTPException(
            status_code=429,
            detail=f"Devnet SOL is available once per {FUND_COOLDOWN_SECONDS}s — try again in a moment",
        )

    wallet = await _ensure_wallet(db, auth)
    platform = solana.load_platform_keypair()
    lamports = int(FUND_SOL * 1e9)

    async with httpx.AsyncClient(timeout=25) as client:
        balance = await solana.get_balance(client, str(platform.pubkey()))
        if balance < lamports + 5000:
            raise HTTPException(
                status_code=503,
                detail="Platform wallet is out of devnet SOL — please try again later",
            )
        signature = await solana.transfer_sol(
            client=client,
            from_keypair=platform,
            to_address=wallet.address,
            lamports=lamports,
        )
        confirmed = await solana.confirm_transaction(client, signature)

    _fund_cooldown[org_key] = now
    return FundResponse(
        wallet_id=str(wallet.id),
        wallet_address=wallet.address,
        amount_sol=FUND_SOL,
        signature=signature,
        confirmed=confirmed,
        explorer_url=_explorer(signature),
    )


class EscrowDemoResponse(BaseModel):
    escrow_id: str
    status: str
    amount_sol: float
    fund_signature: str | None
    fund_explorer_url: str | None
    recipient_address: str


@router.post("/escrow", response_model=EscrowDemoResponse, status_code=201)
async def playground_escrow(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    wallet = await _ensure_wallet(db, auth)
    recipient = _platform_address()

    svc = EscrowService(db)
    escrow = await svc.create_escrow(
        org_id=auth.org_id,
        funder_wallet_id=wallet.id,
        recipient_address=recipient,
        amount_lamports=int(ESCROW_SOL * 1e9),
        conditions={"demo": True, "source": "devnet-playground"},
    )

    return EscrowDemoResponse(
        escrow_id=str(escrow.id),
        status=escrow.status,
        amount_sol=ESCROW_SOL,
        fund_signature=escrow.fund_signature,
        fund_explorer_url=_explorer(escrow.fund_signature) if escrow.fund_signature else None,
        recipient_address=recipient,
    )


class EscrowReleaseResponse(BaseModel):
    escrow_id: str
    status: str
    release_signature: str | None
    release_explorer_url: str | None
    recipient_address: str


@router.post("/escrow/{escrow_id}/release", response_model=EscrowReleaseResponse)
async def playground_escrow_release(
    escrow_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = EscrowService(db)
    escrow = await svc.release_escrow(escrow_id, auth.org_id)
    return EscrowReleaseResponse(
        escrow_id=str(escrow.id),
        status=escrow.status,
        release_signature=escrow.release_signature,
        release_explorer_url=_explorer(escrow.release_signature) if escrow.release_signature else None,
        recipient_address=escrow.recipient_address,
    )


class TransferDemoResponse(BaseModel):
    wallet_id: str
    amount_sol: float
    to_address: str
    signature: str
    confirmed: bool
    explorer_url: str


@router.post("/transfer", response_model=TransferDemoResponse, status_code=201)
async def playground_transfer(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    wallet = await _ensure_wallet(db, auth)
    recipient = _platform_address()
    lamports = int(TRANSFER_SOL * 1e9)

    keypair = WalletManager(db)._decrypt_keypair(wallet)
    async with httpx.AsyncClient(timeout=25) as client:
        balance = await solana.get_balance(client, wallet.address)
        if balance < lamports + 5000:
            raise HTTPException(
                status_code=400,
                detail="Not enough SOL in your wallet — grab devnet SOL first",
            )
        signature = await solana.transfer_sol(
            client=client,
            from_keypair=keypair,
            to_address=recipient,
            lamports=lamports,
        )
        confirmed = await solana.confirm_transaction(client, signature)

    return TransferDemoResponse(
        wallet_id=str(wallet.id),
        amount_sol=TRANSFER_SOL,
        to_address=recipient,
        signature=signature,
        confirmed=confirmed,
        explorer_url=_explorer(signature),
    )
