"""AgentWallet Python SDK -- AI Agent Wallet Infrastructure on Solana."""

from .client import AgentWallet
from .exceptions import (
    AgentWalletAPIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .x402_middleware import X402AutoPay, X402Budget
from .x402_types import (
    X402PaymentInfo,
    X402PaymentProof,
    X402PaymentRequirement,
    X402Response,
)

__all__ = [
    "AgentWallet",
    "AgentWalletAPIError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    # x402 HTTP-native payments
    "X402AutoPay",
    "X402Budget",
    "X402PaymentInfo",
    "X402PaymentProof",
    "X402PaymentRequirement",
    "X402Response",
]

__version__ = "0.1.0"
