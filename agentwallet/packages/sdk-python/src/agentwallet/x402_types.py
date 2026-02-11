"""x402 HTTP-native payment type definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class X402PaymentRequirement:
    """Payment requirement from a 402 Payment Required response."""
    
    network: str          # "solana", "base-sepolia", etc
    token: str            # token address or symbol
    amount: str           # amount in smallest unit
    pay_to: str           # recipient address
    description: str      # what you're paying for


@dataclass
class X402PaymentProof:
    """Payment proof to include in retry request."""
    
    network: str
    token: str
    signature: str        # tx signature
    amount: str


@dataclass
class X402Response:
    """Complete response from x402 payment flow."""
    
    status_code: int
    payment_required: bool
    requirements: list[X402PaymentRequirement] | None
    data: Any             # actual response data after payment
    payment_proof: X402PaymentProof | None
    cost_usd: float       # what was actually paid


@dataclass
class X402PaymentInfo:
    """Payment requirement parsed from 402 response."""
    
    x402_version: str
    description: str
    accepts: list[dict]   # List of accepted payment methods
    raw_body: dict        # Original response body for debugging