"""AIOgram middlewares."""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from core.logger import logger
from core.security import anti_flood, rate_limiter


class LoggingMiddleware(BaseMiddleware):
    """Log every incoming update."""

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:
        user = data.get("event_from_user")
        if user:
            logger.info(f"Update from {user.id} (@{user.username}): {event.__class__.__name__}")
        return await handler(event, data)


class AntiFloodMiddleware(BaseMiddleware):
    """Block flooders."""

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user and anti_flood.is_flood(user.id):
            logger.warning(f"Flood detected from {user.id}")
            return
        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """Per-user rate limit."""

    def __init__(self, rate: int = 30, per: int = 60):
        self.rate = rate
        self.per = per
        self.allowance: Dict[int, Any] = {}

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user and not rate_limiter.is_allowed(user.id):
            logger.warning(f"Rate limit hit: {user.id}")
            return
        return await handler(event, data)


class BanCheckMiddleware(BaseMiddleware):
    """Reject banned users."""

    async def __call__(self, handler, event, data):
        from database.repositories.user_repo import UserRepository
        user = data.get("event_from_user")
        if user:
            repo = UserRepository()
            u = await repo.get(user.id)
            if u and u.get("banned"):
                return
        return await handler(event, data)