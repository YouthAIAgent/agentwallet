"""Application exception hierarchy.

Ported from moltfarm lib/common.py with additions for the AgentWallet domain.
"""


class AgentWalletError(Exception):
    """Base exception for all AgentWallet errors."""


# -- Retry --

class RetryableError(AgentWalletError):
    """Raised when an operation fails but can be retried."""


class RetryExhausted(AgentWalletError):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, func_name: str, attempts: int, last_error: Exception):
        self.func_name = func_name
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"{func_name} failed after {attempts} attempts: {last_error}")


# -- Auth --

class AuthenticationError(AgentWalletError):
    """Invalid or missing credentials."""


class AuthorizationError(AgentWalletError):
    """Insufficient permissions for the requested action."""


# -- Resource --

class NotFoundError(AgentWalletError):
    """Requested resource does not exist."""

    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} not found: {identifier}")


class ConflictError(AgentWalletError):
    """Resource already exists or state conflict."""

    def __init__(self, message: str):
        super().__init__(message)


class ValidationError(AgentWalletError):
    """Input validation failed."""


# -- Transaction --

class InsufficientBalanceError(AgentWalletError):
    """Wallet balance too low for the requested operation."""

    def __init__(self, available: int, required: int):
        self.available = available
        self.required = required
        super().__init__(
            f"Insufficient balance: have {available / 1e9:.4f} SOL, "
            f"need {required / 1e9:.4f} SOL"
        )


class TransactionFailedError(AgentWalletError):
    """Transaction failed on-chain."""


class IdempotencyConflictError(AgentWalletError):
    """Idempotency key already used with different parameters."""


# -- Policy --

class PolicyDeniedError(AgentWalletError):
    """Transaction denied by policy engine."""

    def __init__(self, policy_name: str, reason: str):
        self.policy_name = policy_name
        self.reason = reason
        super().__init__(f"Denied by policy '{policy_name}': {reason}")


class ApprovalRequiredError(AgentWalletError):
    """Transaction requires human approval."""

    def __init__(self, approval_request_id: str):
        self.approval_request_id = approval_request_id
        super().__init__(f"Approval required: {approval_request_id}")


# -- Escrow --

class EscrowStateError(AgentWalletError):
    """Invalid escrow state transition."""


# -- Billing / Tier --

class TierLimitError(AgentWalletError):
    """Organization has reached a tier limit."""

    def __init__(self, resource: str, limit: int, tier: str):
        self.resource = resource
        self.limit = limit
        self.tier = tier
        super().__init__(f"{tier} tier limit: max {limit} {resource}")


class RateLimitError(AgentWalletError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")


# -- ERC-8004 / EVM --

class ERC8004Error(AgentWalletError):
    """ERC-8004 identity/reputation operation failed."""


class EVMTransactionError(AgentWalletError):
    """EVM transaction failed."""
