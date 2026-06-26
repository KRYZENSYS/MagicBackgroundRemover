"""Broadcast, push, DM notifications."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup, InputFile

from src.config.logging import logger
from src.config.settings import settings


@dataclass
class BroadcastResult:
    sent: int = 0
    failed: int = 0
    blocked: int = 0
    total: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send(
        self,
        user_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
        parse_mode: str | None = "HTML",
        disable_notification: bool = False,
        photo: bytes | None = None,
        document: bytes | None = None,
        document_filename: str | None = None,
    ) -> bool:
        """Send a message (or photo/doc) to a user. Returns True on success."""
        try:
            if photo:
                await self.bot.send_photo(
                    user_id,
                    photo=InputFile.__class__.__mro__[0],  # placeholder; use BufferedInputFile below
                    caption=text[:1024],
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification,
                )
            elif document:
                from aiogram.types import BufferedInputFile
                await self.bot.send_document(
                    user_id,
                    document=BufferedInputFile(document, filename=document_filename or "file"),
                    caption=text[:1024],
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification,
                )
            else:
                await self.bot.send_message(
                    user_id,
                    text=text[:4096],
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification,
                )
            return True
        except TelegramAPIError as e:
            logger.warning("Send to %s failed: %s", user_id, e)
            return False

    async def broadcast(
        self,
        user_ids: list[int],
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
        rate_limit: float = 0.05,
        batch_size: int = 25,
        sleep_between: float = 1.0,
        progress_callback=None,
    ) -> BroadcastResult:
        result = BroadcastResult(total=len(user_ids))

        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i : i + batch_size]
            for uid in batch:
                try:
                    await self.bot.send_message(uid, text[:4096], reply_markup=reply_markup, parse_mode="HTML")
                    result.sent += 1
                except TelegramAPIError as e:
                    err = str(e).lower()
                    if "blocked" in err or "deactivated" in err:
                        result.blocked += 1
                    else:
                        result.failed += 1
                    if len(result.errors) < 5:
                        result.errors.append(f"{uid}: {str(e)[:100]}")
                await asyncio.sleep(rate_limit)
            if i + batch_size < len(user_ids):
                await asyncio.sleep(sleep_between)
            if progress_callback:
                try:
                    await progress_callback(i + len(batch), len(user_ids))
                except Exception:
                    pass
        return result

    async def notify_admins(self, text: str, parse_mode: str | None = "HTML") -> None:
        for admin_id in settings.ADMIN_IDS:
            try:
                await self.bot.send_message(admin_id, text[:4096], parse_mode=parse_mode)
            except TelegramAPIError as e:
                logger.warning("Notify admin %s failed: %s", admin_id, e)


notification_service: NotificationService | None = None


__all__ = ["NotificationService", "notification_service", "BroadcastResult"]