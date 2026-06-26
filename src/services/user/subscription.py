"""Subscription service: plans, grant/extend premium."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.subscription import Plan, Subscription
from src.database.models.user import User


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_plan(
        self,
        code: str,
        name: str,
        price: float,
        duration_days: int,
        currency: str = "UZS",
    ) -> Plan:
        plan = Plan(
            code=code,
            name=name,
            price=price,
            currency=currency,
            duration_days=duration_days,
        )
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def get_plan(self, code: str) -> Optional[Plan]:
        result = await self.session.execute(select(Plan).where(Plan.code == code, Plan.is_active == True))
        return result.scalar_one_or_none()

    async def list_plans(self) -> list[Plan]:
        result = await self.session.execute(
            select(Plan).where(Plan.is_active == True).order_by(Plan.price)
        )
        return list(result.scalars())

    async def grant_premium(self, user_id: int, days: int, plan_code: str | None = None) -> User:
        user = await self.session.get(User, user_id)
        if not user:
            raise ValueError("user not found")
        now = datetime.utcnow()
        base = user.premium_until if (user.is_premium and user.premium_until and user.premium_until > now) else now
        new_until = base + timedelta(days=days)
        user.is_premium = True
        user.premium_until = new_until
        sub = Subscription(
            user_id=user_id,
            plan_code=plan_code or "custom",
            started_at=now,
            expires_at=new_until,
            status="active",
        )
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def revoke_premium(self, user_id: int) -> None:
        user = await self.session.get(User, user_id)
        if not user:
            return
        user.is_premium = False
        user.premium_until = None
        await self.session.commit()

    async def extend_premium(self, user_id: int, days: int) -> User:
        return await self.grant_premium(user_id, days)

    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == "active")
            .order_by(Subscription.expires_at.desc())
        )
        return result.scalar_one_or_none()

    async def deactivate_expired(self) -> int:
        """Cron job: mark expired subscriptions as inactive. Returns count."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(User).where(User.is_premium == True, User.premium_until <= now)
        )
        users = list(result.scalars())
        for u in users:
            u.is_premium = False
            u.premium_until = None
        if users:
            await self.session.commit()
        return len(users)


__all__ = ["SubscriptionService"]