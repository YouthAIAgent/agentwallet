"""SDK exception hierarchy."""


class AgentWalletAPIError(Exception):
    """Base error for API responses."""

    def __init__(self, status_code: int, message: str, body: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.body = body or {}
        super().__init__(f"[{status_code}] {message}")


class AuthenticationError(AgentWalletAPIError):
    """401 Unauthorized."""


class AuthorizationError(AgentWalletAPIError):
    """403 Forbidden."""


class NotFoundError(AgentWalletAPIError):
    """404 Not Found."""


class ValidationError(AgentWalletAPIError):
    """422 Validation Error."""


class RateLimitError(AgentWalletAPIError):
    """429 Too Many Requests."""

    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(429, message)


class ConflictError(AgentWalletAPIError):
    """409 Conflict."""
