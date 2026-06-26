"""Analytics: events, counters, summaries."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.analytics import AnalyticsEvent


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def track(self, event_type: str, user_id: int | None = None, properties: dict | None = None) -> None:
        try:
            evt = AnalyticsEvent(
                event_type=event_type,
                user_id=user_id,
                properties=json.dumps(properties or {}),
            )
            self.session.add(evt)
            await self.session.commit()
        except Exception:
            await self.session.rollback()

    async def increment(self, key: str, by: int = 1) -> None:
        await self.track(f"counter:{key}", properties={"delta": by})

    async def count(self, event_type: str, days: int = 1) -> int:
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(AnalyticsEvent.event_type == event_type)
            .where(AnalyticsEvent.created_at >= since)
        )
        return int(result.scalar() or 0)

    async def summary(self, days: int = 7) -> dict:
        since = datetime.utcnow() - timedelta(days=days)
        total_events = await self.session.scalar(
            select(func.count()).select_from(AnalyticsEvent).where(AnalyticsEvent.created_at >= since)
        ) or 0
        active_users = await self.session.scalar(
            select(func.count(func.distinct(AnalyticsEvent.user_id)))
            .where(AnalyticsEvent.created_at >= since)
            .where(AnalyticsEvent.user_id.isnot(None))
        ) or 0
        tool_uses = await self.session.scalar(
            select(func.count()).select_from(AnalyticsEvent)
            .where(AnalyticsEvent.event_type == "tool_used")
            .where(AnalyticsEvent.created_at >= since)
        ) or 0

        # Top tools
        result = await self.session.execute(
            select(AnalyticsEvent.properties, func.count().label("c"))
            .where(AnalyticsEvent.event_type == "tool_used")
            .where(AnalyticsEvent.created_at >= since)
            .group_by(AnalyticsEvent.properties)
            .order_by(func.count().desc())
            .limit(10)
        )
        top_tools = []
        for props, count in result.all():
            try:
                p = json.loads(props or "{}")
                top_tools.append((p.get("tool", "unknown"), int(count)))
            except Exception:
                pass
        return {
            "total_events": int(total_events),
            "active_users": int(active_users),
            "tool_uses": int(tool_uses),
            "top_tools": top_tools,
        }


__all__ = ["AnalyticsService"]