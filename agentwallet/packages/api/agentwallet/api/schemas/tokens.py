"""Token request/response schemas."""

import uuid
from typing import List

from pydantic import BaseModel, Field


class TokenTransferRequest(BaseModel):
    """Request schema for SPL token transfers."""

    from_wallet_id: uuid.UUID = Field(..., description="Source wallet ID")
    to_address: str = Field(..., description="Recipient Solana address")
    token_symbol: str = Field(..., description="Token symbol (USDC, USDT)")
    amount: float = Field(..., gt=0, description="Amount in human-readable format (e.g. 10.50)")
    memo: str | None = Field(None, description="Optional transaction memo")
    idempotency_key: str | None = Field(None, description="Optional idempotency key for deduplication")


class TokenTransferResponse(BaseModel):
    """Response schema for SPL token transfers."""

    id: uuid.UUID = Field(..., description="Transaction ID")
    signature: str | None = Field(None, description="Solana transaction signature")
    status: str = Field(..., description="Transaction status")
    token_symbol: str = Field(..., description="Token symbol")
    amount: float = Field(..., description="Amount transferred (human-readable)")
    fee_amount: float = Field(..., description="Platform fee in SOL")
    from_address: str = Field(..., description="Sender address")
    to_address: str = Field(..., description="Recipient address")
    memo: str | None = Field(None, description="Transaction memo")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")


class TokenBalance(BaseModel):
    """Token balance information."""

    token_symbol: str = Field(..., description="Token symbol")
    mint_address: str = Field(..., description="Token mint address")
    amount: float = Field(..., description="Token balance (human-readable)")
    amount_raw: int = Field(..., description="Token balance in smallest unit")
    decimals: int = Field(..., description="Token decimals")


class TokenBalancesResponse(BaseModel):
    """Response schema for token balances query."""

    wallet_id: uuid.UUID = Field(..., description="Wallet ID")
    address: str = Field(..., description="Wallet Solana address")
    sol_balance: float = Field(..., description="SOL balance")
    tokens: List[TokenBalance] = Field(..., description="List of token balances")


class SupportedToken(BaseModel):
    """Supported token information."""

    symbol: str = Field(..., description="Token symbol")
    name: str = Field(..., description="Token name")
    mint_address: str = Field(..., description="Token mint address")
    decimals: int = Field(..., description="Token decimals")


class SupportedTokensResponse(BaseModel):
    """Response schema for supported tokens."""

    tokens: List[SupportedToken] = Field(..., description="List of supported tokens")
