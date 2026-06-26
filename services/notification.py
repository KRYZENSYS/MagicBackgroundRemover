"""Notification service: emails, broadcasts, alerts."""
from typing import List, Optional
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from core.logger import logger
from core.settings import settings


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_to_user(self, telegram_id: int, text: str, **kwargs) -> bool:
        try:
            await self.bot.send_message(telegram_id, text, **kwargs)
            return True
        except TelegramAPIError as e:
            logger.warning(f"Notify {telegram_id} failed: {e}")
            return False

    async def broadcast(self, user_ids: List[int], text: str, rate_limit: float = 0.05,
                        reply_markup=None) -> tuple[int, int]:
        """Broadcast message to user list. Returns (sent, failed)."""
        sent = 0
        failed = 0
        for uid in user_ids:
            try:
                await self.bot.send_message(uid, text, reply_markup=reply_markup)
                sent += 1
                await _sleep(rate_limit)
            except TelegramAPIError:
                failed += 1
        return sent, failed

    async def admin_log(self, text: str) -> None:
        """Send log message to all admins."""
        for admin_id in settings.ADMIN_IDS:
            try:
                await self.bot.send_message(admin_id, f"\u26a0\ufe0f {text}")
            except TelegramAPIError:
                pass


async def _sleep(seconds: float):
    import asyncio
    await asyncio.sleep(seconds)