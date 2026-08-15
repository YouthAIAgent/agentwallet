"""Presence tracking — anonymous "online now" visitor count for the landing page.

Each visitor heartbeats with an anonymous id; Redis keeps `presence:<id>` alive
for PRESENCE_TTL seconds with the visitor's ISO-3166 alpha-2 country code as the
value. The live snapshot (total + per-country tally) is derived from those keys
and cached briefly so SCAN isn't hammered. Falls back to an in-process dict when
Redis is unavailable (mirrors the rate-limiter resilience pattern).

Merge rule: every heartbeat that reaches Redis is also tracked locally, so
`local_tally[code] <= redis_tally[code]` whenever Redis is healthy; per-code
`max()` therefore never double-counts and still covers Redis-downtime visitors.
"""

import json
import time

from fastapi import Request

from ..core.logging import get_logger
from ..core.redis_client import get_redis

logger = get_logger(__name__)

PRESENCE_TTL = 90  # seconds a visitor counts as online
COUNT_CACHE_TTL = 5  # seconds the snapshot is cached
_PREFIX = "presence:"
_COUNT_KEY = "presence:count"
_COUNTRIES_KEY = "presence:countries"
UNKNOWN = "xx"  # normalized code when no geo header is present

# CDN / proxy geo headers, most specific first
_GEO_HEADERS = (
    "cf-ipcountry",
    "x-vercel-ip-country",
    "x-country-code",
    "cloudfront-viewer-country",
)

# In-process fallback (used when Redis is unavailable): id -> (last_seen, country)
_local_last_seen: dict[str, tuple[float, str]] = {}
_LOCAL_CLEANUP_INTERVAL = 120.0
_local_last_cleanup: float = 0.0


def _cleanup_local(now: float) -> None:
    global _local_last_cleanup
    if now - _local_last_cleanup > _LOCAL_CLEANUP_INTERVAL:
        cutoff = now - PRESENCE_TTL
        stale = [k for k, (ts, _c) in _local_last_seen.items() if ts < cutoff]
        for k in stale:
            del _local_last_seen[k]
        _local_last_cleanup = now


def country_from_request(request: Request) -> str:
    """Best-effort ISO-3166 alpha-2 country code from proxy/CDN headers."""
    for name in _GEO_HEADERS:
        value = (request.headers.get(name) or "").strip().upper()
        if len(value) == 2 and value.isalpha():
            return value
    return UNKNOWN


def _merge_tallies(redis_tally: dict[str, int], local_tally: dict[str, int]) -> dict[str, int]:
    """Per-code max — correct when local ⊆ Redis and when Redis missed heartbeats."""
    codes = set(redis_tally) | set(local_tally)
    return {code: max(redis_tally.get(code, 0), local_tally.get(code, 0)) for code in codes}


class PresenceTracker:
    """Anonymous online-visitor counter with per-country breakdown."""

    async def heartbeat(self, visitor_id: str, country: str = UNKNOWN) -> tuple[int, dict[str, int]]:
        """Register a visitor as online; return (total online, country tally)."""
        country = country if (len(country) == 2 and country.isalpha()) else UNKNOWN
        now = time.time()
        _cleanup_local(now)
        # Always track locally so the count still works without Redis
        _local_last_seen[visitor_id] = (now, country)

        try:
            r = await get_redis()
            await r.set(f"{_PREFIX}{visitor_id}", country, ex=PRESENCE_TTL)
        except Exception:
            logger.debug("presence_redis_unavailable", msg="Redis down — using in-process presence")

        return await self.online_count()

    def _local_snapshot(self) -> dict[str, int]:
        now = time.time()
        _cleanup_local(now)
        cutoff = now - PRESENCE_TTL
        tally: dict[str, int] = {}
        for ts, country in _local_last_seen.values():
            if ts >= cutoff:
                tally[country] = tally.get(country, 0) + 1
        return tally

    async def online_count(self) -> tuple[int, dict[str, int]]:
        """(total online, country tally) — Redis merged with the local fallback."""
        local_tally = self._local_snapshot()
        try:
            r = await get_redis()
            cached = await r.get(_COUNT_KEY)
            cached_countries = await r.get(_COUNTRIES_KEY)
            if cached is not None and cached_countries is not None:
                tally = _merge_tallies(dict(json.loads(cached_countries)), local_tally)
                return max(int(cached), sum(tally.values())), tally

            keys: list[str] = []
            async for k in r.scan_iter(match=f"{_PREFIX}*", count=200):
                keys.append(k)
            redis_tally: dict[str, int] = {}
            if keys:
                vals = await r.mget(keys)
                for v in vals:
                    code = v if (v and len(v) == 2 and v.isalpha()) else UNKNOWN
                    redis_tally[code] = redis_tally.get(code, 0) + 1
            tally = _merge_tallies(redis_tally, local_tally)
            await r.set(_COUNT_KEY, str(sum(tally.values())), ex=COUNT_CACHE_TTL)
            await r.set(_COUNTRIES_KEY, json.dumps(tally), ex=COUNT_CACHE_TTL)
            return sum(tally.values()), tally
        except Exception:
            return sum(local_tally.values()), local_tally


presence = PresenceTracker()
