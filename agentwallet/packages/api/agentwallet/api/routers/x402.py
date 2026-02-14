"""x402 router -- configure pricing, check status, verify payments."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.logging import get_logger
from ...services.x402_server import get_pricing_config, verify_payment_proof
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.x402 import (
    X402ConfigureRequest,
    X402ConfigureResponse,
    X402PriceEntry,
    X402StatusResponse,
    X402VerifyRequest,
    X402VerifyResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/x402", tags=["x402"])


@router.post("/configure", response_model=X402ConfigureResponse, status_code=200)
async def configure_x402_pricing(
    req: X402ConfigureRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Configure x402 payment requirements for API endpoints.

    Sets pricing rules for routes. When enabled, the x402 server middleware
    will return 402 Payment Required for matching routes that don't include
    a valid X-PAYMENT header.
    """
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    config = get_pricing_config()
    pricing_dicts = [entry.model_dump() for entry in req.pricing]

    count = config.configure(
        pricing=pricing_dicts,
        enabled=req.enabled,
        network=req.network,
        default_pay_to=req.default_pay_to,
    )

    logger.info(
        "x402_configured",
        org_id=str(auth.org_id),
        routes=count,
        enabled=req.enabled,
    )

    return X402ConfigureResponse(
        configured_routes=count,
        enabled=req.enabled,
        pricing=req.pricing,
    )


@router.get("/status", response_model=X402StatusResponse)
async def get_x402_status(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Check x402 configuration and payment history.

    Returns current pricing rules, client config, and recent payment records.
    """
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    config = get_pricing_config()
    routes = config.get_all_routes()
    payments = config.get_recent_payments(limit=50)

    pricing_entries = [
        X402PriceEntry(
            route_pattern=r["route_pattern"],
            method=r.get("method", "*"),
            price_lamports=r.get("price_lamports"),
            price_usdc=r.get("price_usdc"),
            description=r.get("description", ""),
            pay_to=r.get("pay_to", ""),
            max_deadline_seconds=r.get("max_deadline_seconds", 60),
        )
        for r in routes
    ]

    return X402StatusResponse(
        enabled=config.enabled,
        server_pricing=pricing_entries,
        client_config=None,
        recent_payments=[],  # Simplified — full payment records need DB backing
        total_incoming_lamports=config.get_total_incoming(),
        total_outgoing_lamports=0,
        payment_count=len(payments),
    )


@router.post("/verify", response_model=X402VerifyResponse)
async def verify_x402_payment(
    req: X402VerifyRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Manually verify an x402 payment proof.

    Decodes the X-PAYMENT header value, validates the transaction signature
    on-chain, and checks that the payment meets the expected amount.
    """
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    result = await verify_payment_proof(
        payment_header=req.payment_header,
        expected_pay_to=req.expected_pay_to,
        expected_amount_lamports=req.expected_amount_lamports,
        expected_amount_usdc=req.expected_amount_usdc,
        network=req.network,
    )

    return X402VerifyResponse(
        valid=result["valid"],
        signature=result.get("signature"),
        payer=result.get("payer"),
        amount_lamports=result.get("amount_lamports"),
        token_mint=result.get("token_mint"),
        error=result.get("error"),
        confirmed_on_chain=result.get("confirmed_on_chain", False),
    )
