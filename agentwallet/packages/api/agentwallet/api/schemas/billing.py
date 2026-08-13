"""Billing request/response schemas."""

import uuid

from pydantic import BaseModel, Field


class Plan(BaseModel):
    """A tier plan with its USDC price."""

    tier: str = Field(..., description="Plan tier key (free, pro, enterprise)")
    name: str = Field(..., description="Plan display name")
    price_usdc: float = Field(..., description="Monthly price in USDC")
    billing_period_days: int = Field(30, description="Billing period length in days")
    agents_limit: int | None = Field(None, description="Max agents (null = unlimited)")
    wallets_limit: int | None = Field(None, description="Max wallets (null = unlimited)")
    tx_monthly_limit: int | None = Field(None, description="Monthly tx limit (null = unlimited)")
    features: list[str] = Field(default_factory=list, description="Plan features")


class PlansResponse(BaseModel):
    """Response with all available plans."""

    plans: list[Plan] = Field(..., description="Available plans")


class SubscribeRequest(BaseModel):
    """Request to subscribe to a tier, paid in USDC."""

    tier: str = Field(..., description="Tier to subscribe to (pro, enterprise)")
    from_wallet_id: uuid.UUID = Field(..., description="Wallet that pays the USDC subscription fee")


class RenewRequest(BaseModel):
    """Request to renew the current subscription."""

    from_wallet_id: uuid.UUID = Field(..., description="Wallet that pays the USDC renewal fee")


class SubscriptionInfo(BaseModel):
    """Current subscription state."""

    id: uuid.UUID | None = Field(None, description="Subscription record ID (null on free tier)")
    tier: str = Field(..., description="Subscribed tier")
    status: str = Field(..., description="Subscription status (active, cancelled, expired, none)")
    amount_usdc: float = Field(0.0, description="Amount paid in USDC")
    period_start: str | None = Field(None, description="Billing period start (ISO)")
    period_end: str | None = Field(None, description="Billing period end (ISO)")
    payment_signature: str | None = Field(None, description="On-chain payment transaction signature")
    auto_renew: bool = Field(False, description="Whether the subscription auto-renews")
    org_tier: str = Field(..., description="Current org tier after this billing state")


class SubscribeResponse(BaseModel):
    """Response for subscribe/renew/cancel operations."""

    subscription: SubscriptionInfo = Field(..., description="Updated subscription state")
    message: str = Field(..., description="Human-readable result message")
