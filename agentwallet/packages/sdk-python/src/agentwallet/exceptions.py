"""SDK exception hierarchy -- every error carries a next-step hint."""

DEFAULT_HINTS = {
    400: "Fix the request payload (check the message body) and retry.",
    401: "Generate a valid API key via POST /api-keys or the dashboard, then retry.",
    403: "Create an API key with the required access level (POST /api-keys), or ask the org owner for permission.",
    404: "Check the resource ID you passed -- it may not exist or may belong to another account.",
    409: "Resolve the conflict (use a different email/idempotency key) and retry.",
    422: "Fix the validation errors in your payload and retry.",
    429: "Wait for the rate-limit window to reset (~60s), then retry, or upgrade your tier.",
    500: "The server hit an unexpected error -- retry in a few seconds, or contact support if it persists.",
    502: "The upstream service failed -- retry in a few seconds, or contact support if it persists.",
    503: "The service is temporarily unavailable -- wait a moment and retry.",
}


class AgentWalletAPIError(Exception):
    """Base error for API responses.

    Attributes:
        status_code: HTTP status code (0 for transport-level errors).
        message: Human-readable error message.
        body: Raw response body, when available.
        hint: Actionable next step the caller can take.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        body: dict | None = None,
        hint: str | None = None,
    ):
        self.status_code = status_code
        self.message = message
        self.body = body or {}
        # An empty string explicitly means "no hint" (e.g. the message itself
        # already carries the next step) -- skip the status-code fallback.
        default_hint = "Retry the operation, or contact support if it persists."
        self.hint = "" if hint == "" else (hint or DEFAULT_HINTS.get(status_code, default_hint))
        detail = f"[{status_code}] {message}"
        if self.hint and self.hint not in str(message):
            detail += f" -- {self.hint}"
        super().__init__(detail)


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

    def __init__(self, message: str, retry_after: int = 60, hint: str | None = None):
        self.retry_after = retry_after
        hint = hint or (
            f"The rate limit is active -- wait ~{retry_after}s, then retry, "
            "or upgrade your tier for higher limits."
        )
        super().__init__(429, message, hint=hint)


class ConflictError(AgentWalletAPIError):
    """409 Conflict."""
