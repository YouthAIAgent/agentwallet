"""x402 HTTP-native auto-pay request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Payment info (returned in 402 responses / discovery)
# ---------------------------------------------------------------------------

class X402PaymentRequirement(BaseModel):
    """Payment requirement returned in 402 responses."""
    scheme: str = "exact"
    network: str = "solana-mainnet"
    max_amount_required: str = Field(..., description="Amount in smallest unit (lamports or token base units)")
    resource: str = Field(..., description="URL of the resource being paid for")
    description: str = ""
    mime_type: str = "application/json"
    pay_to: str = Field(..., description="Solana address to pay")
    required_deadline_seconds: int = Field(default=60, description="Max seconds from now for payment validity")
    output_schema: dict | None = None
    extra: dict = Field(default_factory=dict)


class X402PaymentPayload(BaseModel):
    """Payment proof sent with retry request."""
    x402_version: int = 1
    scheme: str = "exact"
    network: str = "solana-mainnet"
    payload: dict = Field(..., description="Payment proof payload (signature, transaction, etc.)")


# ---------------------------------------------------------------------------
# Server-side pricing configuration
# ---------------------------------------------------------------------------

class X402PriceEntry(BaseModel):
    """Pricing configuration for a single route."""
    route_pattern: str = Field(..., description="Route pattern (e.g. '/api/data/*', exact path, or regex)")
    method: str = Field(default="*", description="HTTP method (* for all, GET, POST, etc.)")
    price_lamports: int | None = Field(default=None, description="Price in lamports (SOL)")
    price_usdc: float | None = Field(default=None, description="Price in USDC")
    description: str = ""
    pay_to: str = Field(..., description="Solana address to receive payments")
    max_deadline_seconds: int = Field(default=60)


class X402ConfigureRequest(BaseModel):
    """Configure x402 pricing for endpoints."""
    pricing: list[X402PriceEntry] = Field(..., description="List of route pricing entries")
    enabled: bool = True
    network: str = "solana-mainnet"
    default_pay_to: str | None = Field(default=None, description="Default payment address if not set per route")


class X402ConfigureResponse(BaseModel):
    configured_routes: int
    enabled: bool
    pricing: list[X402PriceEntry]


# ---------------------------------------------------------------------------
# Client-side spending limits
# ---------------------------------------------------------------------------

class X402SpendingLimit(BaseModel):
    """Spending limit for a domain or endpoint."""
    domain: str = Field(default="*", description="Domain pattern (e.g. 'api.example.com' or '*')")
    max_per_request_lamports: int | None = None
    max_per_request_usdc: float | None = None
    max_daily_lamports: int | None = None
    max_daily_usdc: float | None = None


class X402ClientConfig(BaseModel):
    """Client configuration for auto-pay."""
    wallet_id: uuid.UUID
    enabled: bool = True
    spending_limits: list[X402SpendingLimit] = Field(default_factory=list)
    auto_pay: bool = Field(default=True, description="Automatically pay on 402 responses")
    max_retries: int = Field(default=1, description="Max payment retries per request")


# ---------------------------------------------------------------------------
# Payment verification
# ---------------------------------------------------------------------------

class X402VerifyRequest(BaseModel):
    """Manually verify a payment proof."""
    payment_header: str = Field(..., description="Contents of X-PAYMENT header")
    expected_pay_to: str = Field(..., description="Expected recipient address")
    expected_amount_lamports: int | None = None
    expected_amount_usdc: float | None = None
    network: str = "solana-mainnet"


class X402VerifyResponse(BaseModel):
    valid: bool
    signature: str | None = None
    payer: str | None = None
    amount_lamports: int | None = None
    token_mint: str | None = None
    error: str | None = None
    confirmed_on_chain: bool = False


# ---------------------------------------------------------------------------
# Payment history / status
# ---------------------------------------------------------------------------

class X402PaymentRecord(BaseModel):
    id: uuid.UUID
    direction: str = Field(..., description="'incoming' or 'outgoing'")
    url: str | None = None
    route_pattern: str | None = None
    method: str | None = None
    payer_address: str
    payee_address: str
    amount_lamports: int
    token_mint: str | None = None
    signature: str | None = None
    status: str = "pending"
    created_at: datetime

    model_config = {"from_attributes": True}


class X402StatusResponse(BaseModel):
    enabled: bool
    server_pricing: list[X402PriceEntry] = Field(default_factory=list)
    client_config: X402ClientConfig | None = None
    recent_payments: list[X402PaymentRecord] = Field(default_factory=list)
    total_incoming_lamports: int = 0
    total_outgoing_lamports: int = 0
    payment_count: int = 0


# ---------------------------------------------------------------------------
# MCP / auto-pay request
# ---------------------------------------------------------------------------

class X402MakeRequestInput(BaseModel):
    """Input for make_x402_request MCP tool."""
    url: str = Field(..., description="URL to request")
    method: str = Field(default="GET", description="HTTP method")
    headers: dict = Field(default_factory=dict, description="Additional headers")
    body: str | None = Field(default=None, description="Request body (for POST/PUT)")
    wallet_id: str = Field(..., description="Wallet UUID to pay from")
    max_amount_lamports: int | None = Field(default=None, description="Max lamports willing to pay")
    max_amount_usdc: float | None = Field(default=None, description="Max USDC willing to pay")


class X402MakeRequestOutput(BaseModel):
    """Output from make_x402_request MCP tool."""
    status_code: int
    headers: dict
    body: str
    payment_made: bool = False
    payment_signature: str | None = None
    payment_amount_lamports: int | None = None
