"""AgentWallet Python SDK -- AI Agent Wallet Infrastructure on Solana."""

from .client import AgentWallet
from .exceptions import (
    AgentWalletAPIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

__all__ = [
    "AgentWallet",
    "AgentWalletAPIError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
]

__version__ = "0.1.0"
