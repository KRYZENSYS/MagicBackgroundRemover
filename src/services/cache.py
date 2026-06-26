"""Async cache abstraction. Uses Redis if configured, falls back to in-memory."""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Optional

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis

    REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    REDIS_AVAILABLE = False

from src.config.logging import logger
from src.config.settings import settings


class CacheService:
    """JSON-serialising cache with TTL. In-memory LRU when Redis is disabled."""

    def __init__(self) -> None:
        self._memory: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
        self._redis: Optional[Redis] = None
        self._hits = 0
        self._misses = 0

    async def connect(self) -> None:
        if settings.USE_REDIS and REDIS_AVAILABLE:
            try:
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                await self._redis.ping()
                logger.info("Redis cache connected: %s", settings.REDIS_URL)
            except Exception as e:
                logger.warning("Redis connect failed, falling back to memory: %s", e)
                self._redis = None
        else:
            logger.info("Using in-memory cache")

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()

    async def get(self, key: str, default: Any = None) -> Any:
        try:
            if self._redis:
                v = await self._redis.get(key)
                if v is None:
                    self._misses += 1
                    return default
                self._hits += 1
                return json.loads(v)
            async with self._lock:
                item = self._memory.get(key)
                if not item:
                    self._misses += 1
                    return default
                value, expires = item
                if expires and expires < time.time():
                    self._memory.pop(key, None)
                    self._misses += 1
                    return default
                self._hits += 1
                return value
        except Exception as e:
            logger.warning("Cache get error: %s", e)
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or settings.CACHE_TTL
        try:
            payload = json.dumps(value, default=str)
            if self._redis:
                await self._redis.setex(key, ttl, payload)
                return
            async with self._lock:
                self._memory[key] = (value, time.time() + ttl)
                # Naive cleanup
                if len(self._memory) > 5000:
                    now = time.time()
                    self._memory = {k: v for k, v in self._memory.items() if v[1] > now}
        except Exception as e:
            logger.warning("Cache set error: %s", e)

    async def delete(self, key: str) -> None:
        try:
            if self._redis:
                await self._redis.delete(key)
            async with self._lock:
                self._memory.pop(key, None)
        except Exception as e:
            logger.warning("Cache delete error: %s", e)

    async def clear(self) -> None:
        try:
            if self._redis:
                await self._redis.flushdb()
            async with self._lock:
                self._memory.clear()
        except Exception as e:
            logger.warning("Cache clear error: %s", e)

    async def incr(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        try:
            if self._redis:
                v = await self._redis.incrby(key, amount)
                if ttl:
                    await self._redis.expire(key, ttl)
                return int(v)
        except Exception:
            pass
        async with self._lock:
            current = self._memory.get(key, (0, 0))
            new_val = (int(current[0]) if isinstance(current[0], (int, float)) else 0) + amount
            self._memory[key] = (new_val, time.time() + (ttl or settings.CACHE_TTL))
            return new_val

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "backend": "redis" if self._redis else "memory",
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self._hits / total, 3) if total else 0,
            "size": len(self._memory),
        }


cache = CacheService()

__all__ = ["CacheService", "cache"]