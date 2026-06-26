"""Promo code admin."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.promo import PromoCode


class PromoAdminService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, code: str, days: int, discount: int, limit: int) -> PromoCode:
        promo = PromoCode(
            code=code,
            bonus_days=days,
            discount_percent=discount,
            usage_limit=limit,
            used_count=0,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        self.session.add(promo)
        await self.session.commit()
        await self.session.refresh(promo)
        return promo

    async def list(self) -> list[PromoCode]:
        from sqlalchemy import select
        result = await self.session.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))
        return list(result.scalars())


__all__ = ["PromoAdminService"]