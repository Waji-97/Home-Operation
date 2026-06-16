"""Redis-backed cache with graceful degradation.

If Redis is unreachable the app keeps serving (straight from Notion) instead of
erroring — caching is an optimization, not a hard dependency.
"""
import json

import redis.asyncio as redis

from .config import Settings

# All keys live under one namespace so a publish event can wipe them in one call.
NAMESPACE = "blog"


class Cache:
    def __init__(self, settings: Settings):
        self.s = settings
        self._r: redis.Redis | None = None

    async def connect(self):
        try:
            self._r = redis.from_url(self.s.redis_url, decode_responses=True)
            await self._r.ping()
        except Exception:
            self._r = None  # degrade silently; app still works

    async def close(self):
        if self._r:
            await self._r.aclose()

    def _key(self, *parts: str) -> str:
        return ":".join((NAMESPACE, *parts))

    async def get_json(self, *parts: str):
        if not self._r:
            return None
        try:
            raw = await self._r.get(self._key(*parts))
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def set_json(self, value, *parts: str):
        if not self._r:
            return
        try:
            await self._r.set(self._key(*parts), json.dumps(value), ex=self.s.cache_ttl)
        except Exception:
            pass

    async def invalidate_all(self):
        """Drop every cached entry — called on a Notion webhook."""
        if not self._r:
            return 0
        try:
            keys = [k async for k in self._r.scan_iter(match=f"{NAMESPACE}:*")]
            if keys:
                await self._r.delete(*keys)
            return len(keys)
        except Exception:
            return 0
