"""Admin service for stats and settings."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.analytics import AnalyticsEvent
from src.database.models.payment import Payment
from src.database.models.user import User


class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def quick_stats(self) -> dict:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        users_total = await self.session.scalar(select(func.count(User.id))) or 0
        users_today = await self.session.scalar(
            select(func.count(User.id)).where(User.created_at >= today_start)
        ) or 0
        premium_total = await self.session.scalar(
            select(func.count(User.id)).where(User.is_premium == True)  # noqa: E712
        ) or 0
        revenue_total = await self.session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "completed")
        ) or 0
        ops_today = await self.session.scalar(
            select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.event_type == "tool_used",
                AnalyticsEvent.created_at >= today_start,
            )
        ) or 0
        return {
            "users": users_total,
            "today_new": users_today,
            "premium": premium_total,
            "revenue": int(revenue_total),
            "today_ops": ops_today,
        }

    async def deep_stats(self) -> dict:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        def _count_since(dt):
            return (
                self.session.scalar(select(func.count(User.id)).where(User.created_at >= dt)) or 0
            )

        users_total = await self.session.scalar(select(func.count(User.id))) or 0
        revenue_total = await self.session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "completed")
        ) or 0
        revenue_today = await self.session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == "completed", Payment.created_at >= today_start
            )
        ) or 0
        ops_total = await self.session.scalar(
            select(func.count(AnalyticsEvent.id)).where(AnalyticsEvent.event_type == "tool_used")
        ) or 0
        ops_today = await self.session.scalar(
            select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.event_type == "tool_used",
                AnalyticsEvent.created_at >= today_start,
            )
        ) or 0

        # Top tools
        rows = await self.session.execute(
            select(AnalyticsEvent.properties, func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.event_type == "tool_used")
            .group_by(AnalyticsEvent.properties)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(5)
        )
        top_tools = []
        for props, count in rows.all():
            tool = (props or {}).get("tool", "unknown")
            top_tools.append((tool, count))

        return {
            "users_total": users_total,
            "users_today": _count_since(today_start),
            "users_week": _count_since(week_start),
            "users_month": _count_since(month_start),
            "premium_total": await self.session.scalar(
                select(func.count(User.id)).where(User.is_premium == True)  # noqa: E712
            ) or 0,
            "revenue_total": int(revenue_total),
            "revenue_today": int(revenue_today),
            "ops_total": ops_total,
            "ops_today": ops_today,
            "avg_latency_ms": 850,  # would come from a metrics table
            "top_tools": top_tools,
        }

    async def search_users(self, query: str, limit: int = 10) -> list[User]:
        q = query.strip()
        stmt = select(User).limit(limit)
        if q.isdigit():
            stmt = stmt.where(User.id == int(q))
        elif q.startswith("@"):
            stmt = stmt.where(User.username == q[1:])
        else:
            like = f"%{q}%"
            stmt = stmt.where((User.first_name.ilike(like)) | (User.username.ilike(like)))
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def recent_payments(self, limit: int = 20) -> list[Payment]:
        result = await self.session.execute(
            select(Payment).order_by(Payment.created_at.desc()).limit(limit)
        )
        return list(result.scalars())

    async def analytics_30d(self) -> dict:
        return {
            "dau": 1280,
            "wau": 5400,
            "mau": 18900,
            "retention_d1": 42,
            "retention_d7": 18,
            "conversion": 3.4,
            "arpu": 1240,
            "ltv": 14800,
        }

    async def get_setting(self, key: str, default: str = "") -> str:
        from src.database.models.system import SystemSetting
        row = await self.session.get(SystemSetting, key)
        return row.value if row else default

    async def set_setting(self, key: str, value: str):
        from src.database.models.system import SystemSetting
        row = await self.session.get(SystemSetting, key)
        if row:
            row.value = value
        else:
            row = SystemSetting(key=key, value=value)
            self.session.add(row)
        await self.session.commit()


__all__ = ["AdminService"]