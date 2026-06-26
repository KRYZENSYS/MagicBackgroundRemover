"""i18n middleware: set user language code into handler data."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        sub = data.get("subscription")
        if sub:
            data["lang"] = sub.user.language or "uz"
        else:
            data["lang"] = "uz"
        return await handler(event, data)


__all__ = ["I18nMiddleware"]