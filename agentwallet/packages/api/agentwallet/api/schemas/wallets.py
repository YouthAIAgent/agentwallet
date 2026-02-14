"""Wallet request/response schemas."""

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class WalletCreateRequest(BaseModel):
    agent_id: uuid.UUID | None = None
    wallet_type: Literal["agent", "treasury", "escrow"] = "agent"
    label: str | None = Field(default=None, max_length=255)


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
