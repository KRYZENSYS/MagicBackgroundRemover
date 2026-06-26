"""User middleware: auto-create user record."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.services.user.subscription import SubscriptionService


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session = data.get("session")
        user = data.get("event_from_user")
        if session and user:
            sub_svc = SubscriptionService(session)
            sub, _ = await sub_svc.get_or_create_subscription(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language=user.language_code or "uz",
            )
            data["subscription"] = sub
        return await handler(event, data)


__all__ = ["UserMiddleware"]