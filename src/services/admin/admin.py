"""Admin service: stats, ban, promo, plan CRUD."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.payment import Payment
from src.database.models.promo import PromoCode
from src.database.models.subscription import Plan
from src.database.models.user import User


class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stats(self) -> dict:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        total_users = await self.session.scalar(select(func.count()).select_from(User)) or 0
        today_users = await self.session.scalar(
            select(func.count()).select_from(User).where(User.created_at >= today_start)
        ) or 0
        week_users = await self.session.scalar(
            select(func.count()).select_from(User).where(User.created_at >= week_start)
        ) or 0
        premium_users = await self.session.scalar(
            select(func.count()).select_from(User).where(User.is_premium == True)
        ) or 0

        total_processed = await self.session.scalar(select(func.coalesce(func.sum(User.total_processed), 0))) or 0
        today_processed = await self.session.scalar(
            select(func.coalesce(func.sum(User.daily_processed), 0))
        ) or 0

        revenue = await self.session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "completed")
        ) or 0
        today_revenue = await self.session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.status == "completed")
            .where(Payment.completed_at >= today_start)
        ) or 0

        conversion = (premium_users / total_users * 100) if total_users else 0
        return {
            "total_users": int(total_users),
            "today_users": int(today_users),
            "week_users": int(week_users),
            "premium_users": int(premium_users),
            "total_processed": int(total_processed),
            "today_processed": int(today_processed),
            "total_revenue": float(revenue),
            "today_revenue": float(today_revenue),
            "conversion": float(conversion),
        }

    async def list_users(self, limit: int = 20) -> list[User]:
        result = await self.session.execute(select(User).order_by(User.id.desc()).limit(limit))
        return list(result.scalars())

    async def list_payments(self, limit: int = 20) -> list[Payment]:
        result = await self.session.execute(select(Payment).order_by(Payment.id.desc()).limit(limit))
        return list(result.scalars())

    async def ban_user(self, user_id: int, reason: str = "") -> User:
        user = await self.session.get(User, user_id)
        if not user:
            raise ValueError("user not found")
        user.is_banned = True
        user.ban_reason = reason
        await self.session.commit()
        return user

    async def unban_user(self, user_id: int) -> User:
        user = await self.session.get(User, user_id)
        if not user:
            raise ValueError("user not found")
        user.is_banned = False
        user.ban_reason = None
        await self.session.commit()
        return user

    async def give_premium(self, user_id: int, days: int) -> User:
        from src.services.user.subscription import SubscriptionService
        sub = SubscriptionService(self.session)
        return await sub.grant_premium(user_id, days, "admin")

    async def create_promo(self, code: str, days: int, discount_percent: int, created_by: int) -> PromoCode:
        promo = PromoCode(
            code=code.upper(),
            bonus_days=days,
            discount_percent=discount_percent,
            created_by=created_by,
        )
        self.session.add(promo)
        await self.session.commit()
        await self.session.refresh(promo)
        return promo

    async def create_plan(self, code: str, name: str, price: float, duration_days: int, currency: str) -> Plan:
        plan = Plan(
            code=code,
            name=name,
            price=price,
            currency=currency,
            duration_days=duration_days,
            is_active=True,
        )
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan


__all__ = ["AdminService"]