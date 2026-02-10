"""Transaction request/response schemas."""

import uuid

from pydantic import BaseModel


class TransferSolRequest(BaseModel):
    from_wallet_id: uuid.UUID
    to_address: str
    amount_sol: float
    memo: str | None = None
    idempotency_key: str | None = None


class TransferSplRequest(BaseModel):
    from_wallet_id: uuid.UUID
    to_address: str
    token_mint: str
    amount: float
    memo: str | None = None
    idempotency_key: str | None = None


class BatchTransferRequest(BaseModel):
    transfers: list[TransferSolRequest]


class TransactionResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    agent_id: uuid.UUID | None
    wallet_id: uuid.UUID
    tx_type: str
    status: str
    signature: str | None
    from_address: str
    to_address: str
    amount_lamports: int
    token_mint: str | None
    platform_fee_lamports: int
    memo: str | None
    error: str | None
    created_at: str
    confirmed_at: str | None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    data: list[TransactionResponse]
    total: int
