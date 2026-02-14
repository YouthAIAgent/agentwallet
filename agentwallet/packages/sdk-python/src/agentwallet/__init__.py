"""AgentWallet Python SDK -- AI Agent Wallet Infrastructure on Solana."""

from .client import AgentWallet
from .exceptions import (
    AgentWalletAPIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .types import PDADeriveResult, PDATransferResult, PDAWallet, PDAWalletState
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
    # PDA wallet types
    "PDAWallet",
    "PDAWalletState",
    "PDATransferResult",
    "PDADeriveResult",
    # x402 HTTP-native payments
    "X402AutoPay",
    "X402Budget",
    "X402PaymentInfo",
    "X402PaymentProof",
    "X402PaymentRequirement",
    "X402Response",
]

__version__ = "0.3.0"
