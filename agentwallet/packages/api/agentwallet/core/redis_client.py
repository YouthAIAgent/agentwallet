"""Redis client for caching, rate limiting, and task queues."""

import redis.asyncio as redis

from .config import get_settings

_pool: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create the Redis connection pool."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return _pool


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


class CacheService:
    """Thin wrapper for common cache operations."""

    def __init__(self, redis_client: redis.Redis):
        self.r = redis_client

    async def get(self, key: str) -> str | None:
        return await self.r.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        await self.r.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self.r.delete(key)

    async def incr_with_ttl(self, key: str, ttl: int = 60) -> int:
        """Increment a counter and set TTL if new. Used for rate limiting."""
        pipe = self.r.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        results = await pipe.execute()
        count = results[0]
        current_ttl = results[1]
        if current_ttl == -1:
            await self.r.expire(key, ttl)
        return count
