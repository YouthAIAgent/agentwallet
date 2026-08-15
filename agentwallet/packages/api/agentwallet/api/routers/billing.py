"""Billing router -- on-chain USDC subscription billing.

Organizations pay for tier upgrades in USDC from their own AgentWallet wallet
to the platform wallet. No external payment processor required.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.exceptions import (
    InsufficientBalanceError,
    NotFoundError,
    TransactionFailedError,
    ValidationError,
)
from ...services.usdc_billing import PLANS, UsdcBillingService
from ..middleware.auth import AuthContext, get_auth_context, require_permission
from ..middleware.rate_limit import check_rate_limit
from ..schemas.billing import (
    BillingTier,
    CurrentBillingResponse,
    Plan,
    PlansResponse,
    RenewRequest,
    SubscribeRequest,
    SubscribeResponse,
    SubscriptionInfo,
    TierLimits,
    TiersResponse,
    UsageItem,
)

router = APIRouter(prefix="/billing", tags=["billing"])


def _build_response(info: dict, message: str) -> SubscribeResponse:
    return SubscribeResponse(
        subscription=SubscriptionInfo(**info),
        message=message,
    )


@router.get("/plans", response_model=PlansResponse)
async def list_plans(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
):
    """List all tier plans with USDC pricing."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    return PlansResponse(plans=[Plan(tier=tier, **plan) for tier, plan in PLANS.items()])


@router.get("/tiers", response_model=TiersResponse)
async def list_tiers(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
):
    """List all tiers with dashboard pricing cards (USD monthly + limits)."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    return TiersResponse(
        tiers=[
            BillingTier(
                name=plan["name"],
                price_monthly=plan["price_usdc"],
                limits=TierLimits(
                    agents=plan["agents_limit"],
                    wallets=plan["wallets_limit"],
                    transactions_monthly=plan["tx_monthly_limit"],
                    api_calls_monthly=None,
                ),
                features=plan["features"],
            )
            for plan in PLANS.values()
        ]
    )


@router.get("/current", response_model=CurrentBillingResponse)
async def current_billing(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Current tier + usage for the dashboard billing page."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    from sqlalchemy import func, select

    from ...models.agent import Agent
    from ...models.organization import Organization
    from ...models.transaction import Transaction
    from ...models.wallet import Wallet

    org = await db.get(Organization, auth.org_id)
    if not org:
        raise HTTPException(
            status_code=404,
            detail="Organization not found — check your account or log in again",
        )

    agent_count = (
        await db.execute(select(func.count()).select_from(Agent).where(Agent.org_id == auth.org_id))
    ).scalar_one()
    wallet_count = (
        await db.execute(select(func.count()).select_from(Wallet).where(Wallet.org_id == auth.org_id))
    ).scalar_one()
    tx_count = (
        await db.execute(select(func.count()).select_from(Transaction).where(Transaction.org_id == auth.org_id))
    ).scalar_one()

    plan = PLANS.get(org.tier, PLANS["free"])
    return CurrentBillingResponse(
        tier=org.tier,
        usage={
            "agents": UsageItem(used=int(agent_count), limit=plan["agents_limit"]),
            "wallets": UsageItem(used=int(wallet_count), limit=plan["wallets_limit"]),
            "transactions_monthly": UsageItem(used=int(tx_count), limit=plan["tx_monthly_limit"]),
            "api_calls_monthly": UsageItem(used=0, limit=None),
        },
        amount_due=plan["price_usdc"],
    )


@router.post("/subscribe", response_model=SubscribeResponse, status_code=201)
async def subscribe(
    req: SubscribeRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    _perm: None = Depends(require_permission("billing", "w")),
    db: AsyncSession = Depends(get_db),
):
    """Subscribe to a tier, paying the USDC price on-chain from your wallet."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    service = UsdcBillingService(db)
    try:
        info = await service.subscribe(
            org_id=auth.org_id,
            org_tier=auth.org_tier,
            tier=req.tier,
            from_wallet_id=req.from_wallet_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TransactionFailedError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if req.tier == "free":
        message = "Downgraded to the free tier."
    else:
        message = f"Subscribed to {req.tier} tier — {PLANS[req.tier]['price_usdc']:.0f} USDC paid on-chain."

    return _build_response(info, message)


@router.get("/subscription", response_model=SubscribeResponse)
async def get_subscription(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get the current subscription state and billing-period usage."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    service = UsdcBillingService(db)
    try:
        info = await service.get_subscription(auth.org_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _build_response(info, "Current subscription state.")


@router.post("/renew", response_model=SubscribeResponse)
async def renew(
    req: RenewRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    _perm: None = Depends(require_permission("billing", "w")),
    db: AsyncSession = Depends(get_db),
):
    """Renew the active subscription for another billing period."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    service = UsdcBillingService(db)
    try:
        info = await service.renew(
            org_id=auth.org_id,
            org_tier=auth.org_tier,
            from_wallet_id=req.from_wallet_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TransactionFailedError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return _build_response(info, f"Subscription renewed for another {info['tier']} billing period.")


@router.post("/cancel", response_model=SubscribeResponse)
async def cancel(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    _perm: None = Depends(require_permission("billing", "w")),
    db: AsyncSession = Depends(get_db),
):
    """Cancel the subscription, downgrading the org to free."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    service = UsdcBillingService(db)
    try:
        info = await service.cancel(auth.org_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _build_response(info, "Subscription cancelled — org downgraded to free tier.")
