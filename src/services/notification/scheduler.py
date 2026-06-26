"""Notification scheduler (digest, premium expiry reminders, etc.)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User
from src.database.session import async_session
from src.services.notification.templates import NotificationTemplates

logger = logging.getLogger(__name__)


class NotificationScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self._tasks: list[asyncio.Task] = []

    def start(self):
        self._tasks.append(asyncio.create_task(self._expiry_reminder_loop()))
        self._tasks.append(asyncio.create_task(self._daily_digest_loop()))
        logger.info("NotificationScheduler started with %d tasks", len(self._tasks))

    async def stop(self):
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _expiry_reminder_loop(self):
        while True:
            try:
                await asyncio.sleep(3600)  # 1 hour
                await self.send_premium_expiry_reminders()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("expiry_reminder_loop: %s", e)

    async def send_premium_expiry_reminders(self):
        async with async_session() as session:
            now = datetime.utcnow()
            soon = now + timedelta(days=3)
            result = await session.execute(
                select(User).where(
                    User.is_premium == True,
                    User.premium_until.isnot(None),
                    User.premium_until <= soon,
                    User.premium_until > now,
                    User.notifications_enabled == True,
                )
            )
            users = list(result.scalars())
        for u in users:
            try:
                await self.bot.send_message(
                    u.id,
                    NotificationTemplates.premium_expired(u.language or "uz"),
                )
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.warning("expiry reminder to %s: %s", u.id, e)

    async def _daily_digest_loop(self):
        while True:
            try:
                now = datetime.utcnow()
                # Sleep until 09:00 UTC
                target = now.replace(hour=9, minute=0, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                wait = (target - now).total_seconds()
                await asyncio.sleep(wait)
                await self.send_daily_digest()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("daily_digest_loop: %s", e)

    async def send_daily_digest(self):
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.notifications_enabled == True).limit(500)
            )
            users = list(result.scalars())
        for u in users:
            try:
                await self.bot.send_message(
                    u.id,
                    f"🌅 Xayrli kun! Bugun yangi imkoniyatlar:\n\n"
                    f"📊 Sizda: <b>{u.total_processed}</b> ta rasm ishlandi.\n"
                    f"💎 Premium: {'✅' if u.is_premium else '❌'}\n\n"
                    f"Yangi effektlar sinab ko'ring! /start",
                )
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.warning("digest to %s: %s", u.id, e)


notification_scheduler: NotificationScheduler | None = None


def init_scheduler(bot: Bot) -> NotificationScheduler:
    global notification_scheduler
    notification_scheduler = NotificationScheduler(bot)
    notification_scheduler.start()
    return notification_scheduler


__all__ = ["NotificationScheduler", "init_scheduler"]