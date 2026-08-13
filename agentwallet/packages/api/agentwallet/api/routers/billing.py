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
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.billing import (
    Plan,
    PlansResponse,
    RenewRequest,
    SubscribeRequest,
    SubscribeResponse,
    SubscriptionInfo,
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


@router.post("/subscribe", response_model=SubscribeResponse, status_code=201)
async def subscribe(
    req: SubscribeRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
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
