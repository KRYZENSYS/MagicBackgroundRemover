"""Background notification scheduler (daily reminders, trial nudges)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot

from src.config.logging import logger
from src.database.models.user import User
from src.database.session import async_session
from src.services.notification.service import NotificationService
from src.services.notification.templates import NotificationTemplates


class NotificationScheduler:
    """Runs periodic jobs: expiring premium, daily reminders, inactive re-engagement."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.notifier = NotificationService(bot)
        self._tasks: list[asyncio.Task] = []
        self._stop = False

    def start(self) -> None:
        self._tasks = [
            asyncio.create_task(self._run_daily_check()),
            asyncio.create_task(self._run_premium_expiry_loop()),
            asyncio.create_task(self._run_inactive_reengagement()),
        ]
        logger.info("NotificationScheduler started with %d tasks", len(self._tasks))

    async def stop(self) -> None:
        self._stop = True
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass

    async def _run_daily_check(self) -> None:
        """Run at 09:00 every day."""
        while not self._stop:
            now = datetime.utcnow()
            target = now.replace(hour=4, minute=0, second=0, microsecond=0)  # 09:00 Tashkent
            if now >= target:
                target += timedelta(days=1)
            delay = (target - now).total_seconds()
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                return
            await self._daily_morning_brief()

    async def _daily_morning_brief(self) -> None:
        """Push a brief message at 09:00 to premium users."""
        async with async_session() as s:
            from sqlalchemy import select
            res = await s.execute(
                select(User).where(User.is_premium == True, User.premium_until > datetime.utcnow(), User.is_banned == False)
            )
            users = list(res.scalars().all())
        for u in users:
            try:
                msg = NotificationTemplates.welcome(u.first_name or "do'st", u.language or "uz")
                # Shortened morning greeting
                await self.bot.send_message(u.id, f"☀️ Xayrli kun! Bot tayyor.\n\n{msg[:200]}")
            except Exception as e:
                logger.debug("Morning brief to %s failed: %s", u.id, e)
            await asyncio.sleep(0.05)

    async def _run_premium_expiry_loop(self) -> None:
        """Check every 12 hours for users whose premium expires in 3 days."""
        while not self._stop:
            try:
                await self._notify_premium_expiring()
            except Exception as e:
                logger.exception("Premium expiry loop error: %s", e)
            await asyncio.sleep(12 * 3600)

    async def _notify_premium_expiring(self) -> None:
        async with async_session() as s:
            now = datetime.utcnow()
            soon = now + timedelta(days=3)
            from sqlalchemy import select
            res = await s.execute(
                select(User).where(
                    User.is_premium == True,
                    User.premium_until.between(now, soon),
                    User.is_banned == False,
                )
            )
            users = list(res.scalars().all())
        for u in users:
            try:
                days_left = max(0, (u.premium_until - datetime.utcnow()).days)
                msg = NotificationTemplates.premium_expiring(days_left, u.language or "uz")
                await self.bot.send_message(u.id, msg)
            except Exception:
                pass
            await asyncio.sleep(0.05)

    async def _run_inactive_reengagement(self) -> None:
        """Ping users inactive for 7+ days, max once per 14 days."""
        while not self._stop:
            try:
                await self._reengage_inactive()
            except Exception as e:
                logger.exception("Inactive reengagement error: %s", e)
            await asyncio.sleep(24 * 3600)

    async def _reengage_inactive(self) -> None:
        async with async_session() as s:
            cutoff = datetime.utcnow() - timedelta(days=7)
            cutoff_pinged = datetime.utcnow() - timedelta(days=14)
            from sqlalchemy import select, or_
            res = await s.execute(
                select(User).where(
                    User.is_banned == False,
                    User.last_active_at < cutoff,
                    or_(User.last_notified_at.is_(None), User.last_notified_at < cutoff_pinged),
                ).limit(100)
            )
            users = list(res.scalars().all())
        for u in users:
            try:
                await self.bot.send_message(
                    u.id,
                    "👋 Sizni sog'indik! Yangi funksiyalarni sinab ko'ring: /help",
                )
                async with async_session() as s:
                    user = await s.get(User, u.id)
                    if user:
                        user.last_notified_at = datetime.utcnow()
                        await s.commit()
            except Exception:
                pass
            await asyncio.sleep(0.1)


notification_scheduler: NotificationScheduler | None = None


__all__ = ["NotificationScheduler", "notification_scheduler"]