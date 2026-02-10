"""Rate limiting middleware using Redis sliding window."""

from fastapi import HTTPException, Request

from ...core.logging import get_logger
from ...core.redis_client import CacheService, get_redis

logger = get_logger(__name__)

TIER_LIMITS = {
    "free": 60,
    "pro": 600,
    "enterprise": 6000,
}


async def check_rate_limit(
    request: Request,
    org_id: str,
    tier: str = "free",
) -> None:
    """Check if the request is within rate limits. Raises 429 if exceeded."""
    limit = TIER_LIMITS.get(tier, 60)

    try:
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
