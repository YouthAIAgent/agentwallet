"""Audit middleware -- log API requests for compliance."""

from fastapi import Request

from ...core.logging import get_logger

logger = get_logger(__name__)


async def audit_request(request: Request, org_id: str, actor_id: str) -> None:
    """Log an API request for audit purposes."""
    logger.info(
        "api_request",
        org_id=org_id,
        actor_id=actor_id,
        method=request.method,
        path=request.url.path,
        ip=request.client.host if request.client else "unknown",
    )
