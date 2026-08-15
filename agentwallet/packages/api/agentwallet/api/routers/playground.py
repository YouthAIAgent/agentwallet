"""Devnet Playground — one-click demos that run REAL on-chain transactions.

Every endpoint signs and submits an actual Solana devnet transaction, so
each result carries a signature linkable on the devnet explorer:

    GET  /playground          -> org wallet + balance + platform address
    POST /playground/fund     -> platform wallet -> org wallet (0.01 SOL)
    POST /playground/escrow   -> create + fund an escrow (0.0001 SOL)
    POST /playground/escrow/{escrow_id}/release -> release escrow on-chain
    POST /playground/escrow/{escrow_id}/refund -> refund escrow to funder
    POST /playground/x402     -> pay-per-call AI demo (real x402 payment)
    POST /playground/transfer -> org wallet -> platform (0.0001 SOL)
    POST /playground/usdc     -> mint devnet dUSDC to the org wallet so the
                                 USDC billing demo (subscribe/renew/cancel)
                                 works end to end on devnet

    Amounts stay microscopic on purpose so the platform fund is never
    drained (see FUND_SOL / ESCROW_SOL / TRANSFER_SOL below).
"""

import json
import os
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
from ...services.transaction_engine import TransactionEngine
from ...services.wallet_manager import WalletManager
from ...services.x402_server import verify_payment_proof
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit

router = APIRouter(prefix="/playground", tags=["playground"])

# ----------------------------------------------------------------
# Amounts are intentionally TINY so the platform fund never runs out
# (user-funded: ~5 SOL should serve hundreds of users). Escrow/transfer
# spends are microscopic (0.0001 SOL) — the only real per-user cost is
# the faucet grant (0.01 SOL). Do NOT raise these casually.
# ----------------------------------------------------------------
FUND_SOL = 0.01
ESCROW_SOL = 0.0001
X402_SOL = 0.0001
TRANSFER_SOL = 0.0001
FUND_COOLDOWN_SECONDS = 60
USDC_GRANT = 200.0  # 200 dUSDC per click (pro = 49, enterprise = 299)
USDC_COOLDOWN_SECONDS = 30

# per-org cooldown so nobody can drain the funded platform wallet
_fund_cooldown: dict[str, float] = {}
_usdc_cooldown: dict[str, float] = {}

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
        select(Wallet).where(Wallet.org_id == auth.org_id).order_by(Wallet.created_at.asc()).limit(1)
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
    last_fund = _fund_cooldown.get(org_key, 0)
    if now - last_fund < FUND_COOLDOWN_SECONDS:
        remaining = max(1, int(FUND_COOLDOWN_SECONDS - (now - last_fund)))
        raise HTTPException(
            status_code=429,
            detail=(f"Devnet SOL is available once per {FUND_COOLDOWN_SECONDS}s — try again in {remaining}s"),
            headers={"Retry-After": str(remaining)},
        )

    wallet = await _ensure_wallet(db, auth)
    platform = solana.load_platform_keypair()
    lamports = int(FUND_SOL * 1e9)

    async with httpx.AsyncClient(timeout=25) as client:
        balance = await solana.get_balance(client, str(platform.pubkey()))
        if balance < lamports + 5000:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Platform wallet is out of devnet SOL — please try again later, "
                    "or contact support to refill the custody wallet"
                ),
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


class EscrowRefundResponse(BaseModel):
    escrow_id: str
    status: str
    refund_signature: str | None
    refund_explorer_url: str | None
    funder_wallet_address: str | None


@router.post("/escrow/{escrow_id}/refund", response_model=EscrowRefundResponse)
async def playground_escrow_refund(
    escrow_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Refund an escrow — platform custody returns the funds to the funder's wallet."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    svc = EscrowService(db)
    escrow = await svc.refund_escrow(escrow_id, auth.org_id)
    funder_address = None
    if escrow.funder_wallet_id:
        funder_wallet = await db.get(Wallet, escrow.funder_wallet_id)
        funder_address = funder_wallet.address if funder_wallet else None
    return EscrowRefundResponse(
        escrow_id=str(escrow.id),
        status=escrow.status,
        refund_signature=escrow.refund_signature,
        refund_explorer_url=_explorer(escrow.refund_signature) if escrow.refund_signature else None,
        funder_wallet_address=funder_address,
    )


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


class X402DemoResponse(BaseModel):
    demo: bool
    amount_sol: float
    to_address: str
    payment_signature: str
    payment_confirmed: bool
    payment_explorer_url: str
    verified_on_chain: bool
    verification_error: str | None
    ai_provider: str
    ai_model: str
    ai_response: str


async def _call_demo_llm(prompt: str) -> tuple[str, str, str]:
    """Call a real LLM when configured, else return an honest demo response.

    Uses X402_LLM_* env vars (falling back to OPENAI_COMPAT_*). When no
    upstream is reachable, returns a deterministic, clearly-labeled demo
    answer so the payment rail is always demonstrable end to end.
    Returns (provider, model, response_text).
    """
    base = (os.getenv("X402_LLM_BASE_URL") or os.getenv("OPENAI_COMPAT_BASE_URL") or "").rstrip("/")
    key = os.getenv("X402_LLM_KEY") or os.getenv("OPENAI_COMPAT_API_KEY") or ""
    model = os.getenv("X402_LLM_MODEL") or os.getenv("OPENAI_COMPAT_MODEL") or "demo"
    if base and key:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{base}/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are AgentWallet's AI agent demo. Answer concisely (under 60 words).",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 160,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
                    if content:
                        return "openai-compatible", model, content.strip()
        except Exception:
            pass

    return (
        "demo",
        model,
        "[demo AI · no LLM key configured on the API] "
        "Your 0.0001 SOL payment was verified on-chain and unlocked this pay-per-call gate. "
        "Point the API at any OpenAI-compatible model (X402_LLM_BASE_URL) and this same button "
        "returns a real AI response — same wallet, same escrow, same rail.",
    )


@router.post("/x402", response_model=X402DemoResponse, status_code=201)
async def playground_x402(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """One-click x402 pay-per-call demo — real on-chain payment + AI response.

    Executes the actual x402 flow server-side: build a payment requirement,
    pay from the org wallet (real devnet tx), verify the proof on-chain via
    the same verify_payment_proof used by the x402 gate, then call an LLM
    (real if configured, honest demo otherwise).
    """
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    wallet = await _ensure_wallet(db, auth)
    recipient = _platform_address()
    lamports = int(X402_SOL * 1e9)

    engine = TransactionEngine(db)
    tx = await engine.transfer_sol(
        org_id=auth.org_id,
        org_tier=auth.org_tier,
        wallet_id=wallet.id,
        to_address=recipient,
        amount_lamports=lamports,
        memo="x402 playground pay-per-call",
        idempotency_key=f"x402:playground:{auth.org_id}:{wallet.id}:{lamports}",
    )
    signature = getattr(tx, "signature", None)
    if not signature:
        raise HTTPException(
            status_code=400,
            detail=(
                "Payment transaction has no signature yet — grab devnet SOL via the playground fund demo, then retry"
            ),
        )
    if tx.status == "failed":
        raise HTTPException(status_code=400, detail=f"Payment failed: {tx.error or 'unknown error'}")

    # Verify the payment the way the x402 gate does (on-chain confirm + recipient + amount)
    proof = json.dumps(
        {
            "network": "solana-devnet",
            "token": recipient,
            "signature": signature,
            "amount": str(lamports),
            "timestamp": int(time.time()),
        }
    )
    vr = await verify_payment_proof(
        payment_header=proof,
        expected_pay_to=recipient,
        expected_amount_lamports=lamports,
        network="solana-devnet",
    )

    ai_provider, ai_model, ai_text = await _call_demo_llm(
        "You just received a verified x402 micropayment. Explain in one short line what the user can do now."
    )

    return X402DemoResponse(
        demo=ai_provider == "demo",
        amount_sol=X402_SOL,
        to_address=recipient,
        payment_signature=signature,
        payment_confirmed=tx.status in ("submitted", "confirmed", "completed"),
        payment_explorer_url=_explorer(signature),
        verified_on_chain=bool(vr.get("valid")),
        verification_error=vr.get("error"),
        ai_provider=ai_provider,
        ai_model=ai_model,
        ai_response=ai_text,
    )


class UsdcDemoResponse(BaseModel):
    wallet_id: str
    wallet_address: str
    mint: str
    amount_usdc: float
    signature: str
    confirmed: bool
    explorer_url: str


@router.post("/usdc", response_model=UsdcDemoResponse, status_code=201)
async def playground_usdc(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Mint devnet dUSDC to the org wallet so the billing demo can run.

    The platform keypair is the mint authority of the devnet dUSDC token
    (USDC_MINT_ADDRESS), so this endpoint mints a 200 dUSDC grant directly
    to the user's wallet -- no faucet, no rate limits. That makes the USDC
    billing flow (subscribe -> renew -> cancel) demonstrable end to end.
    """
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    org_key = str(auth.org_id)
    now = time.monotonic()
    last_fund = _usdc_cooldown.get(org_key, 0)
    if now - last_fund < USDC_COOLDOWN_SECONDS:
        remaining = max(1, int(USDC_COOLDOWN_SECONDS - (now - last_fund)))
        raise HTTPException(
            status_code=429,
            detail=(f"Devnet USDC is available once per {USDC_COOLDOWN_SECONDS}s — try again in {remaining}s"),
            headers={"Retry-After": str(remaining)},
        )

    mint = get_settings().usdc_mint_address
    wallet = await _ensure_wallet(db, auth)
    platform = solana.load_platform_keypair()
    amount_raw = int(USDC_GRANT * 1e6)

    async with httpx.AsyncClient(timeout=30) as client:
        signature = await solana.mint_spl_token(
            client=client,
            mint_authority_keypair=platform,
            mint=mint,
            owner_address=wallet.address,
            amount_raw=amount_raw,
            confirm=True,
        )

    _usdc_cooldown[org_key] = now
    return UsdcDemoResponse(
        wallet_id=str(wallet.id),
        wallet_address=wallet.address,
        mint=mint,
        amount_usdc=USDC_GRANT,
        signature=signature,
        confirmed=True,
        explorer_url=_explorer(signature),
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
                detail="Not enough SOL in your wallet — click 'Get 0.01 SOL' first to fund it, then retry",
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
