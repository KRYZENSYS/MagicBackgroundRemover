"""Simple in-memory throttling middleware."""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.config.settings import settings


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit_per_min: int = 60):
        self.rate = rate_limit_per_min
        self._buckets: dict[int, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user or user.id in settings.ADMIN_IDS:
            return await handler(event, data)
        now = time.time()
        bucket = self._buckets[user.id]
        # Drop entries older than 60s
        bucket[:] = [t for t in bucket if now - t < 60]
        if len(bucket) >= self.rate:
            # Silent drop - user is throttled
            return
        bucket.append(now)
        return await handler(event, data)


__all__ = ["ThrottlingMiddleware"]