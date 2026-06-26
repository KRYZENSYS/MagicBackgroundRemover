"""Referral service: create + redeem referrals, leaderboard, promo codes."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import logger
from src.database.models.promo import PromoCode, PromoRedemption
from src.database.models.referral import Referral
from src.database.models.user import User


class ReferralService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_referral(self, referrer_id: int, referred_id: int) -> Referral:
        existing = await self.session.scalar(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        if existing:
            return existing
        ref = Referral(
            referrer_id=referrer_id,
            referred_id=referred_id,
            created_at=datetime.utcnow(),
            reward_days=7,
            reward_granted=False,
        )
        self.session.add(ref)
        # Increment referrer counter
        referrer = await self.session.get(User, referrer_id)
        if referrer:
            referrer.referral_count = (referrer.referral_count or 0) + 1
        await self.session.commit()
        await self._grant_reward(ref)
        return ref

    async def _grant_reward(self, ref: Referral):
        if ref.reward_granted:
            return
        referrer = await self.session.get(User, ref.referrer_id)
        if not referrer:
            return
        from src.services.user.subscription import SubscriptionService
        sub = SubscriptionService(self.session)
        await sub.grant_bonus_days(ref.referrer_id, ref.reward_days)
        ref.reward_granted = True
        await self.session.commit()

    async def top_referrers(self, limit: int = 10) -> list[tuple[User, int]]:
        result = await self.session.execute(
            select(User, User.referral_count)
            .where(User.referral_count > 0)
            .order_by(User.referral_count.desc())
            .limit(limit)
        )
        return [(row[0], row.referral_count) for row in result.all()]

    async def redeem_promo(self, code: str, user_id: int) -> PromoCode:
        from sqlalchemy import update
        result = await self.session.execute(
            select(PromoCode).where(PromoCode.code == code, PromoCode.is_active == True)  # noqa: E712
        )
        promo = result.scalar_one_or_none()
        if not promo:
            raise ValueError("Promo kod topilmadi")
        if promo.expires_at and promo.expires_at < datetime.utcnow():
            raise ValueError("Promo kod muddati tugagan")
        if promo.usage_limit and promo.used_count >= promo.usage_limit:
            raise ValueError("Promo kod limiti tugagan")
        already = await self.session.scalar(
            select(PromoRedemption).where(PromoRedemption.promo_id == promo.id, PromoRedemption.user_id == user_id)
        )
        if already:
            raise ValueError("Bu kod allaqachon ishlatilgan")
        self.session.add(PromoRedemption(promo_id=promo.id, user_id=user_id, redeemed_at=datetime.utcnow()))
        promo.used_count = (promo.used_count or 0) + 1
        await self.session.commit()
        if promo.bonus_days > 0:
            from src.services.user.subscription import SubscriptionService
            sub = SubscriptionService(self.session)
            await sub.grant_bonus_days(user_id, promo.bonus_days)
        return promo


__all__ = ["ReferralService"]