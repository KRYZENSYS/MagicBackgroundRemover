"""Track events to analytics service."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message

from src.services.analytics.analytics import AnalyticsService


class AnalyticsMiddleware(BaseMiddleware):
    """Records every message / callback event."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session = data.get("session")
        user = data.get("event_from_user")
        if session:
            try:
                evt_type = "message" if isinstance(event, Message) else ("callback" if isinstance(event, CallbackQuery) else "event")
                properties = {}
                if isinstance(event, Message) and event.text:
                    properties["text"] = event.text[:100]
                if isinstance(event, CallbackQuery) and event.data:
                    properties["data"] = event.data[:100]
                svc = AnalyticsService(session)
                await svc.track(evt_type, user.id if user else None, properties)
            except Exception:
                pass  # never break the bot for analytics
        return await handler(event, data)


__all__ = ["AnalyticsMiddleware"]