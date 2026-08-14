"""x402 router -- configure pricing, check status, verify payments, auto-pay."""

import json
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.exceptions import NotFoundError, ValidationError
from ...core.logging import get_logger
from ...models.wallet import Wallet
from ...services.transaction_engine import TransactionEngine
from ...services.x402_server import get_pricing_config, verify_payment_proof
from ..middleware.auth import AuthContext, get_auth_context, require_permission
from ..middleware.rate_limit import check_rate_limit
from ..schemas.x402 import (
    X402ConfigureRequest,
    X402ConfigureResponse,
    X402MakeRequestInput,
    X402MakeRequestOutput,
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
    _perm: None = Depends(require_permission("x402", "w")),
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


@router.post("/request", response_model=X402MakeRequestOutput)
async def make_x402_request(
    req: X402MakeRequestInput,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Make an HTTP request with automatic x402 payment.

    Flow: send request -> if 402 -> parse payment requirements -> pay via
    the org's wallet -> retry with payment proof -> return final response.

    Used by the MCP `make_x402_request` tool and direct API consumers.
    """
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    wallet = await db.scalar(select(Wallet).where(Wallet.id == req.wallet_id, Wallet.org_id == auth.org_id))
    if not wallet:
        raise NotFoundError("Wallet not found for this organization")

    headers = dict(req.headers or {})
    body = req.body
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        # Step 1: initial request
        try:
            resp = await client.request(req.method, req.url, headers=headers, content=body)
        except httpx.RequestError as e:
            raise ValidationError(f"Request failed: {e}")

        # Step 2: no payment needed
        if resp.status_code != 402:
            return X402MakeRequestOutput(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=resp.text,
                payment_made=False,
            )

        # Step 3: parse payment requirement from 402 response
        try:
            payment_info = resp.json()
        except Exception:
            raise ValidationError("402 response was not valid JSON")

        accepts = payment_info.get("accepts") or []
        if not accepts:
            raise ValidationError("402 response has no accepted payment methods")

        # Select first acceptable option (prefer USDC, then SOL)
        option = None
        for acc in accepts:
            if acc.get("token_symbol") == "USDC" and acc.get("amount"):
                option = acc
                break
        if option is None:
            for acc in accepts:
                if acc.get("amount") and (acc.get("token_symbol") == "SOL" or acc.get("token") == "SOL"):
                    option = acc
                    break
        if option is None:
            option = accepts[0]

        pay_to = option.get("payTo") or option.get("pay_to")
        amount = option.get("amount")
        token_symbol = option.get("token_symbol", "SOL")
        if not pay_to or not amount:
            raise ValidationError("Payment option missing pay_to or amount")

        # Budget check
        amount_int = int(amount)
        if req.max_amount_lamports is not None and token_symbol == "SOL" and amount_int > req.max_amount_lamports:
            raise ValidationError(
                f"Payment {amount_int} lamports exceeds max_amount_lamports={req.max_amount_lamports}"
            )
        if req.max_amount_usdc is not None and token_symbol == "USDC":
            if amount_int / 1e6 > req.max_amount_usdc:
                raise ValidationError(
                    f"Payment {amount_int / 1e6} USDC exceeds max_amount_usdc={req.max_amount_usdc}"
                )

        # Step 4: execute payment via org wallet
        # Idempotency key must be org-scoped: two different organizations
        # paying the same amount for the same endpoint are distinct payments
        # and must not collide.
        idem = f"x402:{auth.org_id}:{req.wallet_id}:{req.url}:{amount_int}"

        engine = TransactionEngine(db)
        if token_symbol == "USDC":
            from ...services.token_service import TokenService

            tx = await TokenService(db).transfer_token(
                org_id=auth.org_id,
                org_tier=auth.org_tier,
                from_wallet_id=req.wallet_id,
                to_address=pay_to,
                token_symbol="USDC",
                amount=amount_int / 1e6,
                memo=payment_info.get("description", "x402 payment"),
                idempotency_key=idem,
            )
        else:
            tx = await engine.transfer_sol(
                org_id=auth.org_id,
                org_tier=auth.org_tier,
                wallet_id=req.wallet_id,
                to_address=pay_to,
                amount_lamports=amount_int,
                memo=payment_info.get("description", "x402 payment"),
                idempotency_key=idem,
            )

        signature = getattr(tx, "signature", None)
        if not signature:
            raise ValidationError("Payment transaction has no signature yet (pending approval?)")

        # Step 5: retry with payment proof
        payment_header = json.dumps(
            {
                "network": payment_info.get("network", "solana-mainnet"),
                "token": pay_to,
                "signature": signature,
                "amount": amount,
                "timestamp": int(datetime.now(timezone.utc).timestamp()),
            }
        )
        retry_headers = {**headers, "X-PAYMENT": payment_header}
        try:
            retry = await client.request(req.method, req.url, headers=retry_headers, content=body)
        except httpx.RequestError as e:
            raise ValidationError(f"Retry request failed: {e}")

        return X402MakeRequestOutput(
            status_code=retry.status_code,
            headers=dict(retry.headers),
            body=retry.text,
            payment_made=True,
            payment_signature=signature,
            payment_amount_lamports=amount_int,
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
