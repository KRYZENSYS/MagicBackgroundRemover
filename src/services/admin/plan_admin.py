"""Plan admin: create/edit subscription plans."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.subscription import Plan


class PlanAdminService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, code: str, name: str, price: int, currency: str, duration_days: int) -> Plan:
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

    async def toggle(self, plan_id: int, active: bool):
        from sqlalchemy import select
        result = await self.session.execute(select(Plan).where(Plan.id == plan_id))
        plan = result.scalar_one_or_none()
        if plan:
            plan.is_active = active
            await self.session.commit()


__all__ = ["PlanAdminService"]