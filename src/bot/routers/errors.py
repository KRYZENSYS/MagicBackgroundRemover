"""Error router: catch-all for uncaught exceptions and unknown messages."""
from __future__ import annotations

import traceback

from aiogram import F, Router
from aiogram.types import ErrorEvent, Message

from src.config.logging import logger

errors_router = Router(name="errors")


@errors_router.message(F.text.startswith("/"))
async def unknown_command(message: Message, state: FSMContext := None):
    if state:
        await state.clear()
    await message.answer(
        f"❓ Noma'lum buyruq: <code>{message.text[:50]}</code>\n\n"
        "Yordam: /help\nAsosiy menyu: /start"
    )


@errors_router.message()
async def fallback_text(message: Message):
    if message.text and not message.text.startswith("/"):
        await message.answer("📷 Iltimos, rasm yuboring yoki menyudan tanlang.")


@errors_router.errors()
async def error_handler(event: ErrorEvent):
    logger.exception(
        "Unhandled error in update %s: %s\n%s",
        event.update.update_id,
        event.exception,
        "".join(traceback.format_exception(type(event.exception), event.exception, event.exception.__traceback__)),
    )


__all__ = ["errors_router"]