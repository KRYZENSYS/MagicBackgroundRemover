"""Auto-create/update user record on every interaction."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from src.services.user.service import UserService


class UserMiddleware(BaseMiddleware):
    """Ensure a DB row exists for every Telegram user touching the bot."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        session = data.get("session")
        if tg_user and session:
            svc = UserService(session)
            referred_by = data.get("referred_by")
            user, _ = await svc.get_or_create(
                user_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                language=tg_user.language_code or "uz",
                referred_by=referred_by,
            )
            data["db_user"] = user
        return await handler(event, data)


__all__ = ["UserMiddleware"]