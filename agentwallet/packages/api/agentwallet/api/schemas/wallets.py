"""Wallet request/response schemas."""

import uuid

from pydantic import BaseModel


class WalletCreateRequest(BaseModel):
    agent_id: uuid.UUID | None = None
    wallet_type: str = "agent"
    label: str | None = None


class WalletResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    agent_id: uuid.UUID | None
    address: str
    wallet_type: str
    label: str | None
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class WalletBalanceResponse(BaseModel):
    address: str
    sol_balance: float
    lamports: int
    tokens: list[dict] = []


class WalletListResponse(BaseModel):
    data: list[WalletResponse]
    total: int
