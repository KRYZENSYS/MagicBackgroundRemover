"""Referral / promo code service."""
from __future__ import annotations

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import (
    REFERRAL_BONUS_DAYS_INVITER,
    REFERRAL_BONUS_DAYS_INVITEE,
)
from src.database.models.referral import Referral, PromoCode, PromoRedemption
from src.database.models.user import User
from src.exceptions import AlreadyExistsError, NotFoundError, ValidationError


class ReferralService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _gen_code(length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        # Remove confusable chars
        alphabet = alphabet.translate(str.maketrans("", "", "O0I1L"))
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def create_referral(self, inviter_id: int, invitee_id: int) -> Referral:
        if inviter_id == invitee_id:
            raise ValidationError("Cannot refer yourself")
        ref = Referral(inviter_id=inviter_id, invitee_id=invitee_id, created_at=datetime.utcnow())
        self.session.add(ref)
        try:
            await self.session.commit()
            await self.session.refresh(ref)
        except Exception:
            await self.session.rollback()
            raise AlreadyExistsError("Referral already exists")

        # Award inviter
        await self.session.execute(
            update(User)
            .where(User.id == inviter_id)
            .values(referral_count=User.referral_count + 1)
        )
        # Award bonus days to invitee
        inviter = await self.session.get(User, inviter_id)
        invitee = await self.session.get(User, invitee_id)
        if inviter and invitee and not invitee.trial_used:
            # Add bonus to inviter's premium_until if active, else give free days
            if inviter.premium_until and inviter.premium_until > datetime.utcnow():
                inviter.premium_until += timedelta(days=REFERRAL_BONUS_DAYS_INVITER)
            # Give invitee a trial
            invitee.trial_used = True
            invitee.is_premium = True
            invitee.premium_until = datetime.utcnow() + timedelta(days=REFERRAL_BONUS_DAYS_INVITEE)
        await self.session.commit()
        return ref

    async def referral_count(self, user_id: int) -> int:
        res = await self.session.execute(
            select(func.count(Referral.id)).where(Referral.inviter_id == user_id)
        )
        return int(res.scalar_one() or 0)

    async def referrals_of(self, user_id: int, limit: int = 50) -> list[Referral]:
        res = await self.session.execute(
            select(Referral).where(Referral.inviter_id == user_id).order_by(Referral.created_at.desc()).limit(limit)
        )
        return list(res.scalars().all())

    async def top_referrers(self, limit: int = 10) -> list[tuple[User, int]]:
        res = await self.session.execute(
            select(User, User.referral_count)
            .where(User.referral_count > 0)
            .order_by(User.referral_count.desc())
            .limit(limit)
        )
        return [(r[0], int(r[1])) for r in res.all()]

    # Promo codes
    async def create_promo(
        self,
        bonus_days: int = 0,
        discount_percent: int = 0,
        max_uses: int = 1,
        valid_days: int = 30,
        code: Optional[str] = None,
    ) -> PromoCode:
        code = code or self._gen_code()
        promo = PromoCode(
            code=code,
            bonus_days=bonus_days,
            discount_percent=discount_percent,
            max_uses=max_uses,
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=valid_days),
            created_at=datetime.utcnow(),
        )
        self.session.add(promo)
        await self.session.commit()
        await self.session.refresh(promo)
        return promo

    async def get_promo(self, code: str) -> PromoCode:
        res = await self.session.execute(select(PromoCode).where(PromoCode.code == code.upper(), PromoCode.is_active == True))
        promo = res.scalar_one_or_none()
        if not promo:
            raise NotFoundError("Promo code not found")
        return promo

    async def redeem_promo(self, code: str, user_id: int) -> PromoCode:
        promo = await self.get_promo(code)
        now = datetime.utcnow()
        if promo.valid_from and promo.valid_from > now:
            raise ValidationError("Promo code not yet active")
        if promo.valid_until and promo.valid_until < now:
            raise ValidationError("Promo code expired")
        if promo.current_uses >= promo.max_uses:
            raise ValidationError("Promo code fully used")
        # Check single-use-per-user
        existing = await self.session.execute(
            select(PromoRedemption).where(PromoRedemption.promo_id == promo.id, PromoRedemption.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise ValidationError("Already redeemed")

        redemption = PromoRedemption(
            promo_id=promo.id,
            user_id=user_id,
            redeemed_at=now,
        )
        self.session.add(redemption)
        promo.current_uses += 1
        await self.session.commit()
        await self.session.refresh(promo)

        # Apply bonus days to user
        if promo.bonus_days > 0:
            user = await self.session.get(User, user_id)
            if user:
                if user.premium_until and user.premium_until > now:
                    user.premium_until += timedelta(days=promo.bonus_days)
                else:
                    user.premium_until = now + timedelta(days=promo.bonus_days)
                user.is_premium = True
                await self.session.commit()
        return promo

    async def deactivate_promo(self, code: str) -> None:
        promo = await self.get_promo(code)
        promo.is_active = False
        await self.session.commit()


referral_service = None


__all__ = ["ReferralService", "referral_service"]