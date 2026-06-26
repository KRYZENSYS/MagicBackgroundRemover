"""Analytics service: events + counters."""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.analytics import AnalyticsEvent, AnalyticsCounter


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def track(self, event_type: str, user_id: int | None = None, properties: dict | None = None):
        evt = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            properties=properties or {},
            created_at=datetime.utcnow(),
        )
        self.session.add(evt)
        await self.session.commit()

    async def increment(self, name: str, by: int = 1):
        from datetime import date
        today = date.today()
        result = await self.session.execute(
            select(AnalyticsCounter).where(AnalyticsCounter.name == name, AnalyticsCounter.day == today)
        )
        row = result.scalar_one_or_none()
        if row:
            row.value += by
        else:
            row = AnalyticsCounter(name=name, day=today, value=by)
            self.session.add(row)
        await self.session.commit()

    async def get_counter(self, name: str, day=None) -> int:
        from datetime import date
        if day is None:
            day = date.today()
        v = await self.session.scalar(
            select(AnalyticsCounter.value).where(AnalyticsCounter.name == name, AnalyticsCounter.day == day)
        )
        return int(v or 0)


__all__ = ["AnalyticsService"]