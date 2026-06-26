"""Throttling middleware: per-user message rate limit."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate: float = 1.5):
        self.rate = rate
        self._last: Dict[int, float] = {}
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user or not isinstance(event, Message):
            return await handler(event, data)
        now = time.monotonic()
        async with self._lock:
            last = self._last.get(user.id, 0)
            if now - last < self.rate:
                return None
            self._last[user.id] = now
        return await handler(event, data)


__all__ = ["ThrottlingMiddleware"]