"""PDA Wallet request/response schemas."""

import uuid

from pydantic import BaseModel, Field


class PDAWalletCreateRequest(BaseModel):
    authority_wallet_id: uuid.UUID
    agent_id_seed: str = Field(..., min_length=1, max_length=64)
    spending_limit_per_tx: int = Field(..., gt=0)
    daily_limit: int = Field(..., gt=0)
    agent_id: uuid.UUID | None = None


class PDAWalletResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    pda_address: str
    authority_wallet_id: uuid.UUID
    agent_id: uuid.UUID | None
    agent_id_seed: str
    spending_limit_per_tx: int
    daily_limit: int
    bump: int
    is_active: bool
    tx_signature: str | None
    created_at: str

    model_config = {"from_attributes": True}


class PDAWalletStateResponse(BaseModel):
    pda_address: str
    authority: str
    org: str
    agent_id: str
    spending_limit_per_tx: int
    daily_limit: int
    daily_spent: int
    last_reset_day: int
    is_active: bool
    bump: int
    sol_balance: float


class PDATransferRequest(BaseModel):
    recipient: str = Field(..., min_length=32, max_length=64)
    amount_lamports: int = Field(..., gt=0)


class PDATransferResponse(BaseModel):
    signature: str
    confirmed: bool


class PDAUpdateLimitsRequest(BaseModel):
    spending_limit_per_tx: int | None = Field(None, gt=0)
    daily_limit: int | None = Field(None, gt=0)
    is_active: bool | None = None


class PDADeriveRequest(BaseModel):
    org_pubkey: str = Field(..., min_length=32, max_length=64)
    agent_id_seed: str = Field(..., min_length=1, max_length=64)


class PDADeriveResponse(BaseModel):
    pda_address: str
    bump: int


class PDAWalletListResponse(BaseModel):
    data: list[PDAWalletResponse]
    total: int
