"""Analytics service: events, metrics, daily aggregation."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import logger
from src.database.models.analytics import AnalyticsEvent, DailyStats


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def track(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        properties: Optional[dict] = None,
    ) -> None:
        """Record an event for later aggregation."""
        try:
            evt = AnalyticsEvent(
                event_type=event_type,
                user_id=user_id,
                properties=properties or {},
                created_at=datetime.utcnow(),
            )
            self.session.add(evt)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.warning("Analytics track failed: %s", e)

    async def increment(self, metric: str, by: int = 1, day: Optional[datetime] = None) -> None:
        """Increment a daily counter."""
        day = (day or datetime.utcnow()).date()
        existing = await self.session.execute(
            select(DailyStats).where(DailyStats.metric == metric, DailyStats.day == day)
        )
        stat = existing.scalar_one_or_none()
        if stat:
            stat.value = (stat.value or 0) + by
        else:
            stat = DailyStats(metric=metric, day=day, value=by)
            self.session.add(stat)
        await self.session.commit()

    async def today(self, metric: str) -> int:
        day = datetime.utcnow().date()
        res = await self.session.execute(
            select(DailyStats.value).where(DailyStats.metric == metric, DailyStats.day == day)
        )
        return int(res.scalar_one() or 0)

    async def range_(self, metric: str, days: int = 30) -> list[tuple[datetime, int]]:
        since = (datetime.utcnow() - timedelta(days=days)).date()
        res = await self.session.execute(
            select(DailyStats.day, DailyStats.value)
            .where(DailyStats.metric == metric, DailyStats.day >= since)
            .order_by(DailyStats.day)
        )
        return [(r[0], int(r[1])) for r in res.all()]

    async def top_events(self, limit: int = 20, days: int = 7) -> list[tuple[str, int]]:
        since = datetime.utcnow() - timedelta(days=days)
        res = await self.session.execute(
            select(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.created_at >= since)
            .group_by(AnalyticsEvent.event_type)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(limit)
        )
        return [(r[0], int(r[1])) for r in res.all()]

    async def active_users(self, days: int = 1) -> int:
        since = datetime.utcnow() - timedelta(days=days)
        res = await self.session.execute(
            select(func.count(func.distinct(AnalyticsEvent.user_id)))
            .where(AnalyticsEvent.created_at >= since, AnalyticsEvent.user_id.isnot(None))
        )
        return int(res.scalar_one() or 0)

    async def tool_usage(self, days: int = 30) -> dict[str, int]:
        since = datetime.utcnow() - timedelta(days=days)
        res = await self.session.execute(
            select(AnalyticsEvent.properties["tool"].astext, func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.event_type == "tool_used", AnalyticsEvent.created_at >= since)
            .group_by(AnalyticsEvent.properties["tool"].astext)
        )
        return {r[0]: int(r[1]) for r in res.all() if r[0]}

    async def retention(self, weeks: int = 4) -> dict:
        # Simple cohort: users who came back N days after joining
        result = {}
        for w in range(weeks):
            target_day = datetime.utcnow() - timedelta(weeks=w)
            res = await self.session.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT user_id)
                    FROM analytics_events
                    WHERE DATE(created_at) = :day
                    """
                ),
                {"day": target_day.date()},
            )
            result[f"week_-{w}"] = int(res.scalar_one() or 0)
        return result

    async def daily_summary(self) -> dict:
        today = datetime.utcnow().date()
        res = await self.session.execute(
            select(DailyStats.metric, DailyStats.value).where(DailyStats.day == today)
        )
        return {r[0]: int(r[1]) for r in res.all()}


analytics_service = None

__all__ = ["AnalyticsService", "analytics_service"]