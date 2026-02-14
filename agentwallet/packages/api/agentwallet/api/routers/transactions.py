"""Transaction router -- SOL/SPL transfers, batch operations."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.exceptions import (
    ApprovalRequiredError,
    IdempotencyConflictError,
    InsufficientBalanceError,
    PolicyDeniedError,
)
from ...services.transaction_engine import TransactionEngine
from ..middleware.auth import AuthContext, get_auth_context
from ..middleware.rate_limit import check_rate_limit
from ..schemas.transactions import (
    BatchTransferRequest,
    TransactionListResponse,
    TransactionResponse,
    TransferSolRequest,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _tx_to_response(tx) -> TransactionResponse:
    return TransactionResponse(
        id=tx.id,
        org_id=tx.org_id,
        agent_id=tx.agent_id,
        wallet_id=tx.wallet_id,
        tx_type=tx.tx_type,
        status=tx.status,
        signature=tx.signature,
        from_address=tx.from_address,
        to_address=tx.to_address,
        amount_lamports=tx.amount_lamports,
        token_mint=tx.token_mint,
        platform_fee_lamports=tx.platform_fee_lamports,
        memo=tx.memo,
        error=tx.error,
        created_at=tx.created_at.isoformat(),
        confirmed_at=tx.confirmed_at.isoformat() if tx.confirmed_at else None,
    )


@router.post("/transfer-sol", response_model=TransactionResponse, status_code=201)
async def transfer_sol(
    req: TransferSolRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Transfer SOL from a managed wallet."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    engine = TransactionEngine(db)
    try:
        tx = await engine.transfer_sol(
            org_id=auth.org_id,
            org_tier=auth.org_tier,
            wallet_id=req.from_wallet_id,
            to_address=req.to_address,
            amount_lamports=int(req.amount_sol * 1e9),
            memo=req.memo,
            idempotency_key=req.idempotency_key,
        )
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

    return _tx_to_response(tx)


@router.post("/batch-transfer", response_model=list[TransactionResponse])
async def batch_transfer(
    req: BatchTransferRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Execute multiple SOL transfers in parallel (semaphore-gated)."""
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)

    engine = TransactionEngine(db)
    transfers = [
        {
            "from_wallet_id": t.from_wallet_id,
            "to_address": t.to_address,
            "amount_sol": t.amount_sol,
            "memo": t.memo,
            "idempotency_key": t.idempotency_key,
        }
        for t in req.transfers
    ]
    results = await engine.batch_transfer_sol(
        org_id=auth.org_id,
        org_tier=auth.org_tier,
        transfers=transfers,
    )
    return [_tx_to_response(tx) for tx in results]


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    request: Request,
    agent_id: uuid.UUID | None = None,
    wallet_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    engine = TransactionEngine(db)
    txs, total = await engine.list_transactions(
        org_id=auth.org_id,
        agent_id=agent_id,
        wallet_id=wallet_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return TransactionListResponse(
        data=[_tx_to_response(tx) for tx in txs],
        total=total,
    )


@router.get("/{tx_id}", response_model=TransactionResponse)
async def get_transaction(
    tx_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request, str(auth.org_id), auth.org_tier)
    engine = TransactionEngine(db)
    tx = await engine.get_transaction(tx_id, auth.org_id)
    return _tx_to_response(tx)
