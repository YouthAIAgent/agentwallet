"""Rate limiting middleware using Redis sliding window with in-process fallback."""

import time
from collections import defaultdict

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
_redis_last_check: float = 0.0
_REDIS_RECHECK_INTERVAL = 60.0  # Re-check Redis availability every 60 seconds

# In-process fallback rate limiter (used when Redis is unavailable)
_local_counters: dict[str, list[float]] = defaultdict(list)
_LOCAL_CLEANUP_INTERVAL = 300.0  # Cleanup stale entries every 5 minutes
_local_last_cleanup: float = 0.0


def _local_rate_check(key: str, limit: int, window: int = 60) -> bool:
    """In-process sliding window rate limiter. Returns True if within limit."""
    global _local_last_cleanup

    now = time.monotonic()

    # Periodic cleanup of stale keys
    if now - _local_last_cleanup > _LOCAL_CLEANUP_INTERVAL:
        stale_keys = [k for k, v in _local_counters.items() if not v or v[-1] < now - window * 2]
        for k in stale_keys:
            del _local_counters[k]
        _local_last_cleanup = now

    # Remove timestamps outside the window
    timestamps = _local_counters[key]
    cutoff = now - window
    while timestamps and timestamps[0] < cutoff:
        timestamps.pop(0)

    if len(timestamps) >= limit:
        return False

    timestamps.append(now)
    return True


async def _check_redis() -> bool:
    """Test Redis connectivity, re-check periodically."""
    global _redis_available, _redis_last_check

    now = time.monotonic()

    # Use cached result if checked recently
    if _redis_available is not None and (now - _redis_last_check) < _REDIS_RECHECK_INTERVAL:
        return _redis_available

    try:
        r = await get_redis()
        await r.ping()
        if not _redis_available:
            logger.info("redis_reconnected", msg="Rate limiting using Redis again")
        _redis_available = True
    except Exception:
        if _redis_available is not False:
            logger.warning("redis_unavailable", msg="Rate limiting falling back to in-process limiter")
        _redis_available = False

    _redis_last_check = now
    return _redis_available


async def check_rate_limit(
    request: Request,
    org_id: str,
    tier: str = "free",
) -> None:
    """Check if the request is within rate limits. Raises 429 if exceeded.

    Uses Redis when available, falls back to in-process sliding window.
    """
    limit = TIER_LIMITS.get(tier, 60)
    rate_key = f"rl:{org_id}:{request.url.path}"

    # Try Redis first
    if await _check_redis():
        try:
            from ...core.redis_client import CacheService

            r = await get_redis()
            cache = CacheService(r)
            count = await cache.incr_with_ttl(rate_key, ttl=60)

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
            return  # Within limit
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("rate_limit_redis_error", error=str(e), msg="Falling back to local limiter")

    # Fallback: in-process rate limiter
    if not _local_rate_check(rate_key, limit):
        logger.warning(
            "rate_limit_exceeded_local",
            org_id=org_id,
            path=request.url.path,
            limit=limit,
        )
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({limit}/min). Upgrade tier for higher limits.",
            headers={"Retry-After": "60"},
        )
