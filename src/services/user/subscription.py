"""Subscription and plan management."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import (
    PLAN_LIFETIME_DAYS,
    PLAN_MONTHLY_DAYS,
    PLAN_YEARLY_DAYS,
)
from src.database.models.payment import Payment, Plan, Subscription
from src.exceptions import NotFoundError, ValidationError


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # Plans
    async def create_plan(
        self,
        code: str,
        name: str,
        price: float,
        duration_days: int,
        currency: str = "UZS",
        description: Optional[str] = None,
    ) -> Plan:
        plan = Plan(
            code=code,
            name=name,
            price=price,
            currency=currency,
            duration_days=duration_days,
            description=description,
        )
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def get_plan(self, code: str) -> Plan:
        res = await self.session.execute(select(Plan).where(Plan.code == code, Plan.is_active == True))
        plan = res.scalar_one_or_none()
        if not plan:
            raise NotFoundError(f"Plan {code} not found")
        return plan

    async def list_plans(self) -> list[Plan]:
        res = await self.session.execute(select(Plan).where(Plan.is_active == True).order_by(Plan.price))
        return list(res.scalars().all())

    async def deactivate_plan(self, code: str) -> None:
        plan = await self.get_plan(code)
        plan.is_active = False
        await self.session.commit()

    # Subscriptions
    async def subscribe(
        self,
        user_id: int,
        plan_code: str,
        payment_id: Optional[int] = None,
    ) -> Subscription:
        plan = await self.get_plan(plan_code)
        now = datetime.utcnow()
        # Check for active subscription
        res = await self.session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                Subscription.ends_at > now,
            )
        )
        existing = res.scalar_one_or_none()
        if existing:
            # Extend
            existing.ends_at = existing.ends_at + timedelta(days=plan.duration_days)
            existing.plan_id = plan.id
            await self.session.commit()
            return existing

        sub = Subscription(
            user_id=user_id,
            plan_id=plan.id,
            starts_at=now,
            ends_at=now + timedelta(days=plan.duration_days),
            is_active=True,
            payment_id=payment_id,
        )
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)

        # Mirror onto user table
        from src.database.models.user import User

        user = await self.session.get(User, user_id)
        if user:
            user.is_premium = True
            user.premium_until = sub.ends_at
            await self.session.commit()
        return sub

    async def cancel(self, user_id: int) -> None:
        now = datetime.utcnow()
        res = await self.session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
            )
        )
        for sub in res.scalars().all():
            sub.is_active = False
            sub.cancelled_at = now
        await self.session.commit()

        from src.database.models.user import User

        user = await self.session.get(User, user_id)
        if user and user.is_premium and user.premium_until and user.premium_until <= now:
            user.is_premium = False
            user.premium_until = None
            await self.session.commit()

    async def is_active(self, user_id: int) -> bool:
        now = datetime.utcnow()
        res = await self.session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                Subscription.ends_at > now,
            )
        )
        return bool(res.scalar_one())

    async def active_for(self, user_id: int) -> Optional[Subscription]:
        now = datetime.utcnow()
        res = await self.session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                Subscription.ends_at > now,
            )
        )
        return res.scalar_one_or_none()

    async def history(self, user_id: int, limit: int = 20) -> list[Subscription]:
        res = await self.session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())

    async def expiring_soon(self, days: int = 3) -> list[Subscription]:
        now = datetime.utcnow()
        threshold = now + timedelta(days=days)
        res = await self.session.execute(
            select(Subscription).where(
                Subscription.is_active == True,
                Subscription.ends_at.between(now, threshold),
            )
        )
        return list(res.scalars().all())

    async def cleanup_expired(self) -> int:
        now = datetime.utcnow()
        from sqlalchemy import update

        result = await self.session.execute(
            update(Subscription)
            .where(Subscription.is_active == True, Subscription.ends_at <= now)
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount or 0

    # Seed default plans
    async def ensure_default_plans(self) -> None:
        existing = await self.session.execute(select(Plan).limit(1))
        if existing.scalar_one_or_none():
            return

        defaults = [
            ("monthly", "Monthly", 19900, PLAN_MONTHLY_DAYS, "UZS"),
            ("quarterly", "Quarterly", 49900, 90, "UZS"),
            ("yearly", "Yearly", 179900, PLAN_YEARLY_DAYS, "UZS"),
            ("lifetime", "Lifetime", 499900, PLAN_LIFETIME_DAYS, "UZS"),
        ]
        for code, name, price, days, cur in defaults:
            self.session.add(Plan(code=code, name=name, price=price, duration_days=days, currency=cur))
        await self.session.commit()


subscription_service = None

__all__ = ["SubscriptionService", "subscription_service"]