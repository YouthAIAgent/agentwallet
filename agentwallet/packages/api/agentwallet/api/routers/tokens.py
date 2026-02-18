"""Token router -- SPL token transfers and balance queries."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.exceptions import (
    ApprovalRequiredError,
    IdempotencyConflictError,
    InsufficientBalanceError,
    NotFoundError,
    PolicyDeniedError,
    ValidationError,
)
from ...services.token_service import TokenService
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.tokens import (
    SupportedToken,
    SupportedTokensResponse,
    TokenBalancesResponse,
    TokenTransferRequest,
    TokenTransferResponse,
)

router = APIRouter(prefix="/tokens", tags=["tokens"])


def _tx_to_token_response(tx, token_symbol: str, amount: float, fee_sol: float) -> TokenTransferResponse:
    """Convert Transaction model to TokenTransferResponse."""
    return TokenTransferResponse(
        id=tx.id,
        signature=tx.signature,
        status=tx.status,
        token_symbol=token_symbol,
        amount=amount,
        fee_amount=fee_sol,
        from_address=tx.from_address,
        to_address=tx.to_address,
        memo=tx.memo,
        created_at=tx.created_at.isoformat(),
    )


@router.post("/transfer", response_model=TokenTransferResponse, status_code=201)
async def transfer_token(
    req: TokenTransferRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Transfer USDC/USDT between wallets."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    token_service = TokenService(db)
    try:
        tx = await token_service.transfer_token(
            org_id=auth.org_id,
            org_tier=auth.org_tier,
            from_wallet_id=req.from_wallet_id,
            to_address=req.to_address,
            token_symbol=req.token_symbol,
            amount=req.amount,
            memo=req.memo,
            idempotency_key=req.idempotency_key,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PolicyDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ApprovalRequiredError as e:
        raise HTTPException(
            status_code=202,
            detail={
                "status": "approval_required",
                "approval_request_id": e.approval_request_id,
            },
        )
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IdempotencyConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Convert platform fee from lamports to SOL
    fee_sol = tx.platform_fee_lamports / 1e9

    return _tx_to_token_response(tx, req.token_symbol, req.amount, fee_sol)


@router.get("/balances/{wallet_id}", response_model=TokenBalancesResponse)
async def get_token_balances(
    wallet_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Get all token balances for a wallet."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    token_service = TokenService(db)

    # Get wallet and validate ownership
    try:
        wallet = await token_service.wallet_mgr.get_wallet(wallet_id, auth.org_id)
        if wallet.org_id != auth.org_id:
            raise HTTPException(status_code=404, detail="Wallet not found")

        # Get all token balances
        balances = await token_service.get_all_token_balances(wallet.address)

        return TokenBalancesResponse(
            wallet_id=wallet_id,
            address=wallet.address,
            sol_balance=balances["sol_balance"],
            tokens=balances["tokens"],
        )

    except NotFoundError:
        raise HTTPException(status_code=404, detail="Wallet not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balances: {str(e)}")


@router.get("/supported", response_model=SupportedTokensResponse)
async def list_supported_tokens(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
):
    """List all supported stablecoins with mint addresses."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    tokens = []
    for symbol, config in TokenService.SUPPORTED_TOKENS.items():
        tokens.append(
            SupportedToken(
                symbol=symbol,
                name=config["name"],
                mint_address=config["mint"],
                decimals=config["decimals"],
            )
        )

    return SupportedTokensResponse(tokens=tokens)
