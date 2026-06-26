"""Payment, plan and promo code repository."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Payment, Plan, PromoCode, Subscription
from core.security import generate_promo_code


class PlanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, code: str, name: str, price: float, duration_days: int,
                     currency: str = "UZS", features: list = None, is_lifetime: bool = False) -> Plan:
        plan = Plan(code=code, name=name, price=price, duration_days=duration_days,
                    currency=currency, features=features or [], is_lifetime=is_lifetime)
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def get(self, plan_id: int) -> Optional[Plan]:
        result = await self.session.execute(select(Plan).where(Plan.id == plan_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Plan]:
        result = await self.session.execute(select(Plan).where(Plan.code == code))
        return result.scalar_one_or_none()

    async def list_active(self) -> List[Plan]:
        result = await self.session.execute(select(Plan).where(Plan.is_active == True))
        return list(result.scalars().all())


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, plan_id: int, amount: float, provider: str,
                     currency: str = "UZS", transaction_id: Optional[str] = None) -> Payment:
        p = Payment(user_id=user_id, plan_id=plan_id, amount=amount, provider=provider,
                    currency=currency, transaction_id=transaction_id, status="pending")
        self.session.add(p)
        await self.session.commit()
        await self.session.refresh(p)
        return p

    async def complete(self, payment_id: int, transaction_id: Optional[str] = None) -> None:
        await self.session.execute(update(Payment).where(Payment.id == payment_id).values(
            status="completed", transaction_id=transaction_id, completed_at=datetime.utcnow()
        ))
        await self.session.commit()

    async def fail(self, payment_id: int, reason: str = "") -> None:
        await self.session.execute(update(Payment).where(Payment.id == payment_id).values(
            status="failed", payload={"error": reason}
        ))
        await self.session.commit()

    async def total_revenue(self) -> float:
        result = await self.session.execute(
            select(func.sum(Payment.amount)).where(Payment.status == "completed")
        )
        return float(result.scalar_one() or 0.0)

    async def revenue_today(self) -> float:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.sum(Payment.amount)).where(Payment.status == "completed", Payment.completed_at >= today_start)
        )
        return float(result.scalar_one() or 0.0)


class PromoCodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, discount_percent: int = 0, bonus_days: int = 0,
                     max_uses: int = 1, valid_days: int = 30) -> PromoCode:
        code = generate_promo_code(10)
        from datetime import timedelta
        promo = PromoCode(
            code=code, discount_percent=discount_percent, bonus_days=bonus_days,
            max_uses=max_uses, valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=valid_days),
        )
        self.session.add(promo)
        await self.session.commit()
        await self.session.refresh(promo)
        return promo

    async def get(self, code: str) -> Optional[PromoCode]:
        result = await self.session.execute(select(PromoCode).where(PromoCode.code == code.upper()))
        return result.scalar_one_or_none()

    async def use(self, code: str) -> bool:
        promo = await self.get(code)
        if not promo or not promo.is_active:
            return False
        if promo.current_uses >= promo.max_uses:
            return False
        if promo.valid_until and promo.valid_until < datetime.utcnow():
            return False
        promo.current_uses += 1
        await self.session.commit()
        return True