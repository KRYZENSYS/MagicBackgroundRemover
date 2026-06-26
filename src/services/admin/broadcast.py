"""Broadcast service: send a message to all users with rate limiting."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User

logger = logging.getLogger(__name__)


class BroadcastService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.batch_size = 25
        self.delay = 0.05  # 50ms between messages

    async def broadcast_all(self, text: str) -> tuple[int, int]:
        result = await self.session.execute(select(User.id).where(User.is_banned == False))
        user_ids = [int(uid) for uid in result.scalars()]
        sent = 0
        failed = 0
        for i, uid in enumerate(user_ids, 1):
            try:
                await self.bot.send_message(uid, text)
                sent += 1
            except TelegramAPIError as e:
                logger.warning("Broadcast to %s failed: %s", uid, e)
                failed += 1
            except Exception as e:
                logger.exception("Broadcast unexpected error for %s: %s", uid, e)
                failed += 1
            if i % self.batch_size == 0:
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(self.delay)
        return sent, failed

    async def broadcast_to(self, user_ids: list[int], text: str) -> tuple[int, int]:
        sent = failed = 0
        for uid in user_ids:
            try:
                await self.bot.send_message(uid, text)
                sent += 1
            except Exception as e:
                logger.warning("Broadcast to %s: %s", uid, e)
                failed += 1
            await asyncio.sleep(self.delay)
        return sent, failed


__all__ = ["BroadcastService"]