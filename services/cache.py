"""Cache service with optional Redis backend."""
import json
from typing import Any, Optional

from core.settings import settings
from core.logger import logger


class CacheService:
    """In-memory cache with optional Redis."""

    def __init__(self):
        self._memory: dict[str, Any] = {}
        self._redis = None
        if settings.REDIS_URL:
            try:
                import redis.asyncio as redis_async
                self._redis = redis_async.from_url(settings.REDIS_URL, decode_responses=True)
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis unavailable, using memory: {e}")

    async def get(self, key: str) -> Optional[Any]:
        try:
            if self._redis:
                data = await self._redis.get(key)
                return json.loads(data) if data else None
            return self._memory.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        ttl = ttl or settings.CACHE_TTL
        try:
            data = json.dumps(value, default=str)
            if self._redis:
                await self._redis.setex(key, ttl, data)
            else:
                self._memory[key] = value
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def delete(self, key: str) -> None:
        try:
            if self._redis:
                await self._redis.delete(key)
            self._memory.pop(key, None)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    async def clear(self) -> None:
        try:
            if self._redis:
                await self._redis.flushdb()
            self._memory.clear()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    async def close(self):
        if self._redis:
            await self._redis.close()


cache = CacheService()