"""Rate limiting middleware using Redis sliding window."""

from fastapi import HTTPException, Request

from ...core.logging import get_logger
from ...core.redis_client import get_redis

logger = get_logger(__name__)

TIER_LIMITS = {
    "free": 60,
    "pro": 600,
    "enterprise": 6000,
}

_redis_available: bool | None = None


async def _check_redis() -> bool:
    """Test Redis connectivity once, cache the result."""
    global _redis_available
    if _redis_available is not None:
        return _redis_available
    try:
        r = await get_redis()
        await r.ping()
        _redis_available = True
    except Exception:
        _redis_available = False
        logger.warning("redis_unavailable", msg="Rate limiting disabled (no Redis)")
    return _redis_available


async def check_rate_limit(
    request: Request,
    org_id: str,
    tier: str = "free",
) -> None:
    """Check if the request is within rate limits. Raises 429 if exceeded."""
    if not await _check_redis():
        return  # Fail open — no Redis

    limit = TIER_LIMITS.get(tier, 60)

    try:
        from ...core.redis_client import CacheService

        r = await get_redis()
        cache = CacheService(r)
        key = f"rl:{org_id}:{request.url.path}"
        count = await cache.incr_with_ttl(key, ttl=60)

        if count > limit:
            logger.warning(
                "rate_limit_exceeded",
                org_id=org_id,
                path=request.url.path,
                count=count,
                limit=limit,
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({limit}/min). Upgrade tier for higher limits.",
                headers={"Retry-After": "60"},
            )
    except HTTPException:
        raise
    except Exception as e:
        # Fail open if Redis is down
        logger.warning("rate_limit_check_failed", error=str(e))
