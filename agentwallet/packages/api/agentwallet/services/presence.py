"""Presence tracking — anonymous "online now" visitor count for the landing page.

Each visitor heartbeats with an anonymous id; Redis keeps `presence:<id>` alive
for PRESENCE_TTL seconds. The live count is the number of those keys, cached
briefly so SCAN isn't hammered. Falls back to an in-process dict when Redis is
unavailable (mirrors the rate-limiter resilience pattern).
"""

import time

from ..core.logging import get_logger
from ..core.redis_client import get_redis

logger = get_logger(__name__)

PRESENCE_TTL = 90  # seconds a visitor counts as online
COUNT_CACHE_TTL = 5  # seconds the count result is cached
_PREFIX = "presence:"
_COUNT_KEY = "presence:count"

# In-process fallback (used when Redis is unavailable)
_local_last_seen: dict[str, float] = {}
_LOCAL_CLEANUP_INTERVAL = 120.0
_local_last_cleanup: float = 0.0


def _cleanup_local(now: float) -> None:
    global _local_last_cleanup
    if now - _local_last_cleanup > _LOCAL_CLEANUP_INTERVAL:
        cutoff = now - PRESENCE_TTL
        stale = [k for k, v in _local_last_seen.items() if v < cutoff]
        for k in stale:
            del _local_last_seen[k]
        _local_last_cleanup = now


class PresenceTracker:
    """Anonymous online-visitor counter."""

    async def heartbeat(self, visitor_id: str) -> int:
        """Register a visitor as online and return the current online count."""
        now = time.time()
        _cleanup_local(now)
        # Always track locally so the count still works without Redis
        _local_last_seen[visitor_id] = now

        try:
            r = await get_redis()
            await r.set(f"{_PREFIX}{visitor_id}", "1", ex=PRESENCE_TTL)
        except Exception:
            logger.debug("presence_redis_unavailable", msg="Redis down — using in-process presence")

        return await self.online_count()

    def _local_count(self) -> int:
        now = time.time()
        _cleanup_local(now)
        cutoff = now - PRESENCE_TTL
        return sum(1 for v in _local_last_seen.values() if v >= cutoff)

    async def online_count(self) -> int:
        """Number of visitors seen within the presence window.

        Returns the max of Redis and local counts — equivalent in production
        (every heartbeat that reaches Redis is also tracked locally), and
        correct when Redis is down, misconfigured, or just started.
        """
        local = self._local_count()
        try:
            r = await get_redis()
            cached = await r.get(_COUNT_KEY)
            if cached is not None:
                return max(int(cached), local)
            count = 0
            async for _ in r.scan_iter(match=f"{_PREFIX}*", count=200):
                count += 1
            await r.set(_COUNT_KEY, str(count), ex=COUNT_CACHE_TTL)
            return max(count, local)
        except Exception:
            return local


presence = PresenceTracker()
