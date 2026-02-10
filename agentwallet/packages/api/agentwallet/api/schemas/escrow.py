"""Escrow request/response schemas."""

import uuid

from pydantic import BaseModel


class EscrowCreateRequest(BaseModel):
    funder_wallet_id: uuid.UUID
    recipient_address: str
    amount_sol: float
    token_mint: str | None = None
    arbiter_address: str | None = None
    conditions: dict = {}
    expires_in_hours: int = 24


class EscrowActionRequest(BaseModel):
    action: str  # release, refund, dispute
    reason: str | None = None


class EscrowResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    funder_wallet_id: uuid.UUID
    recipient_address: str
    arbiter_address: str | None
    escrow_address: str | None
    amount_lamports: int
    token_mint: str | None
    status: str
    conditions: dict
    fund_signature: str | None
    release_signature: str | None
    refund_signature: str | None
    dispute_reason: str | None
    expires_at: str | None
    funded_at: str | None
    completed_at: str | None
    created_at: str

    model_config = {"from_attributes": True}


class EscrowListResponse(BaseModel):
    data: list[EscrowResponse]
    total: int
