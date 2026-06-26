"""Broadcast service: queue messages, send in batches."""
from __future__ import annotations

import asyncio

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import logger
from src.database.models.broadcast import Broadcast
from src.database.models.user import User


class BroadcastService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def queue_broadcast(self, text: str) -> int:
        bc = Broadcast(text=text, status="pending")
        self.session.add(bc)
        await self.session.commit()
        total = await self.session.scalar(select(__import__("sqlalchemy").func.count(User.id))) or 0
        bc.target_count = total
        await self.session.commit()
        return total

    async def start_pending(self) -> int:
        result = await self.session.execute(select(Broadcast).where(Broadcast.status == "pending"))
        bcs = list(result.scalars())
        sent = 0
        for bc in bcs:
            bc.status = "in_progress"
            await self.session.commit()
            users_result = await self.session.execute(select(User.id))
            user_ids = [r[0] for r in users_result.all()]
            sent = await self._dispatch(bc.id, user_ids, bc.text)
            bc.status = "done"
            bc.sent_count = sent
            await self.session.commit()
        return sent

    async def _dispatch(self, broadcast_id: int, user_ids: list[int], text: str) -> int:
        from src.bot import bot as bot_module  # late import

        bot = getattr(bot_module, "bot_instance", None)
        if bot is None:
            logger.warning("Bot not initialized; cannot broadcast")
            return 0
        sent = 0
        sem = asyncio.Semaphore(25)

        async def _send(uid: int):
            nonlocal sent
            async with sem:
                try:
                    await bot.send_message(uid, text)
                    sent += 1
                    await asyncio.sleep(0.04)
                except Exception:
                    pass

        await asyncio.gather(*[_send(uid) for uid in user_ids])
        return sent


__all__ = ["BroadcastService"]