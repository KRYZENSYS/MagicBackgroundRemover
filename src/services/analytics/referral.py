"""Referral service: create referral, redeem promo, top users."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.promo import PromoCode, PromoRedemption
from src.database.models.referral import Referral
from src.database.models.user import User


class ReferralService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_referral(self, referrer_id: int, referred_id: int) -> Referral:
        if referrer_id == referred_id:
            raise ValueError("self-referral")
        # Idempotent: check if exists
        existing = await self.session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("already_referred")
        ref = Referral(referrer_id=referrer_id, referred_id=referred_id)
        self.session.add(ref)
        # Award both with +7 days premium
        from src.services.user.subscription import SubscriptionService
        sub_svc = SubscriptionService(self.session)
        await sub_svc.grant_premium(referrer_id, 7, "referral_bonus")
        await sub_svc.grant_premium(referred_id, 7, "referral_welcome")
        # Bump counters
        ru = await self.session.get(User, referrer_id)
        if ru:
            ru.referral_count += 1
        await self.session.commit()
        await self.session.refresh(ref)
        return ref

    async def redeem_promo(self, code: str, user_id: int) -> PromoCode:
        result = await self.session.execute(
            select(PromoCode).where(PromoCode.code == code.upper(), PromoCode.is_active == True)
        )
        promo = result.scalar_one_or_none()
        if not promo:
            raise ValueError("invalid_code")
        if promo.max_uses and promo.current_uses >= promo.max_uses:
            raise ValueError("code_exhausted")
        # Check user already redeemed
        existing = await self.session.execute(
            select(PromoRedemption).where(
                PromoRedemption.promo_id == promo.id,
                PromoRedemption.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("already_redeemed")
        redemption = PromoRedemption(promo_id=promo.id, user_id=user_id)
        self.session.add(redemption)
        promo.current_uses += 1
        if promo.bonus_days > 0:
            from src.services.user.subscription import SubscriptionService
            sub_svc = SubscriptionService(self.session)
            await sub_svc.grant_premium(user_id, promo.bonus_days, f"promo:{promo.code}")
        await self.session.commit()
        return promo

    async def top_referrers(self, limit: int = 10) -> list[tuple[User, int]]:
        result = await self.session.execute(
            select(User, func.count(Referral.id).label("c"))
            .join(Referral, Referral.referrer_id == User.id)
            .group_by(User.id)
            .order_by(func.count(Referral.id).desc())
            .limit(limit)
        )
        return [(u, int(c)) for u, c in result.all()]


__all__ = ["ReferralService"]