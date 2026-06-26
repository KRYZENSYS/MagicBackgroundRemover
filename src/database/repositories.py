"""Repository layer - one class per aggregate, hides SQL from the rest of the app."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import (
    ImageTool,
    PaymentProvider,
    PaymentStatus,
    PlanTier,
    SubscriptionPlan,
    UserStatus,
)
from src.database.models import (
    AuditLog,
    Broadcast,
    GlobalStat,
    ImageJob,
    ImagePreset,
    Payment,
    PromoCode,
    Referral,
    Subscription,
    User,
)


# ============== USER ==============

class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_referral_code(self, code: str) -> Optional[User]:
        stmt = select(User).where(User.referral_code == code)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: str = "uz",
        referred_by: Optional[int] = None,
    ) -> User:
        referral_code = secrets.token_urlsafe(8)[:12]
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            referral_code=referral_code,
            referred_by=referred_by,
        )
        self.session.add(user)
        await self.session.flush()
        await self._increment_stat("total_users")
        return user

    async def update_activity(self, user: User) -> None:
        user.last_active = datetime.utcnow()
        await self.session.flush()

    async def set_language(self, user: User, language: str) -> None:
        user.language = language
        await self.session.flush()

    async def set_premium(
        self,
        user: User,
        plan: SubscriptionPlan,
        days: Optional[int] = None,
    ) -> None:
        if plan == SubscriptionPlan.LIFETIME:
            user.plan_tier = PlanTier.VIP
            user.subscription_until = None
        else:
            user.plan_tier = max(user.plan_tier, PlanTier.PREMIUM)
            base = user.subscription_until or datetime.utcnow()
            days = days or (365 if plan == SubscriptionPlan.YEARLY else 30)
            user.subscription_until = base + timedelta(days=days)
        await self.session.flush()
        await self._increment_stat("total_premium")

    async def set_trial(self, user: User, days: int) -> None:
        user.plan_tier = PlanTier.TRIAL
        base = datetime.utcnow()
        user.subscription_until = base + timedelta(days=days)
        user.trial_used = True
        await self.session.flush()

    async def ban(self, user: User, reason: str) -> None:
        user.is_banned = True
        user.ban_reason = reason
        await self.session.flush()

    async def unban(self, user: User) -> None:
        user.is_banned = False
        user.ban_reason = None
        await self.session.flush()

    async def warn(self, user: User) -> int:
        user.is_warned = True
        user.warning_count += 1
        await self.session.flush()
        return user.warning_count

    async def clear_warnings(self, user: User) -> None:
        user.is_warned = False
        user.warning_count = 0
        await self.session.flush()

    async def increment_processed(self, user: User) -> None:
        user.total_processed += 1
        today = datetime.utcnow().date()
        last = user.last_active.date() if user.last_active else None
        if last == today:
            user.daily_processed += 1
        else:
            user.daily_processed = 1
        await self.session.flush()
        await self._increment_stat("total_processed")

    async def list_active(self, limit: int = 100, offset: int = 0) -> Sequence[User]:
        stmt = (
            select(User)
            .where(User.is_banned == False)  # noqa: E712
            .order_by(User.last_active.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def count(self, where=None) -> int:
        stmt = select(func.count(User.id))
        if where is not None:
            stmt = stmt.where(where)
        return (await self.session.execute(stmt)).scalar_one()

    async def search(self, query: str, limit: int = 25) -> Sequence[User]:
        like = f"%{query}%"
        stmt = (
            select(User)
            .where(
                or_(
                    User.username.ilike(like),
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                    User.telegram_id == int(query) if query.isdigit() else False,
                )
            )
            .limit(limit)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def _increment_stat(self, field: str) -> None:
        stmt = update(GlobalStat).where(GlobalStat.id == 1).values(**{field: getattr(GlobalStat, field) + 1})
        await self.session.execute(stmt)


# ============== IMAGE JOBS ==============

class ImageJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: int,
        tool: ImageTool,
        params: Optional[dict] = None,
        input_file_id: Optional[str] = None,
        input_path: Optional[str] = None,
        file_size_in: int = 0,
        is_batch: bool = False,
        batch_size: int = 1,
    ) -> ImageJob:
        job = ImageJob(
            user_id=user_id,
            tool=tool.value,
            params=params or {},
            input_file_id=input_file_id,
            input_path=input_path,
            file_size_in=file_size_in,
            is_batch=is_batch,
            batch_size=batch_size,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def complete(
        self,
        job: ImageJob,
        output_file_id: Optional[str] = None,
        output_path: Optional[str] = None,
        duration_ms: int = 0,
        file_size_out: int = 0,
    ) -> None:
        job.output_file_id = output_file_id
        job.output_path = output_path
        job.duration_ms = duration_ms
        job.file_size_out = file_size_out
        job.success = True
        await self.session.flush()

    async def fail(self, job: ImageJob, error: str) -> None:
        job.success = False
        job.error_message = error[:1000]
        await self.session.flush()

    async def user_history(self, user_id: int, limit: int = 50) -> Sequence[ImageJob]:
        stmt = (
            select(ImageJob)
            .where(ImageJob.user_id == user_id)
            .order_by(ImageJob.created_at.desc())
            .limit(limit)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def daily_count(self, tool: Optional[ImageTool] = None) -> int:
        today = datetime.utcnow().date()
        stmt = select(func.count(ImageJob.id)).where(func.date(ImageJob.created_at) == today)
        if tool:
            stmt = stmt.where(ImageJob.tool == tool.value)
        return (await self.session.execute(stmt)).scalar_one()

    async def popular_tools(self, limit: int = 10) -> list[tuple[str, int]]:
        stmt = (
            select(ImageJob.tool, func.count(ImageJob.id).label("cnt"))
            .group_by(ImageJob.tool)
            .order_by(func.count(ImageJob.id).desc())
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(r[0], r[1]) for r in rows]


# ============== PAYMENTS ==============

class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: int,
        provider: PaymentProvider,
        plan: SubscriptionPlan,
        amount: float,
        currency: str = "USD",
        external_id: Optional[str] = None,
        promo_code: Optional[str] = None,
        discount_percent: int = 0,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            provider=provider.value,
            external_id=external_id,
            plan=plan.value,
            amount=amount,
            currency=currency,
            promo_code=promo_code,
            discount_percent=discount_percent,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def mark_completed(self, payment: Payment, external_id: Optional[str] = None) -> None:
        payment.status = PaymentStatus.COMPLETED.value
        if external_id:
            payment.external_id = external_id
        payment.completed_at = datetime.utcnow()
        await self.session.flush()

    async def mark_failed(self, payment: Payment, reason: str) -> None:
        payment.status = PaymentStatus.FAILED.value
        payment.raw_payload = {**(payment.raw_payload or {}), "failure_reason": reason}
        await self.session.flush()

    async def by_external_id(self, external_id: str) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.external_id == external_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def user_payments(self, user_id: int, limit: int = 20) -> Sequence[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def total_revenue(self) -> float:
        stmt = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(Payment.status == PaymentStatus.COMPLETED.value)
        return float((await self.session.execute(stmt)).scalar_one())


# ============== SUBSCRIPTIONS ==============

class SubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: int,
        plan: SubscriptionPlan,
        provider: PaymentProvider,
        payment_id: Optional[int] = None,
        days: Optional[int] = None,
    ) -> Subscription:
        if plan == SubscriptionPlan.LIFETIME:
            expires = None
        else:
            days = days or (365 if plan == SubscriptionPlan.YEARLY else 30)
            expires = datetime.utcnow() + timedelta(days=days)

        sub = Subscription(
            user_id=user_id,
            plan=plan.value,
            provider=provider.value,
            payment_id=payment_id,
            expires_at=expires,
            is_active=True,
        )
        self.session.add(sub)
        await self.session.flush()
        return sub


# ============== REFERRALS ==============

class ReferralRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(self, referrer_id: int, referred_id: int) -> Referral:
        ref = Referral(referrer_id=referrer_id, referred_id=referred_id)
        self.session.add(ref)
        await self.session.flush()
        return ref

    async def leaderboard(self, limit: int = 10) -> list[tuple[int, str, int]]:
        stmt = (
            select(User.telegram_id, User.first_name, User.referral_count)
            .where(User.referral_count > 0)
            .order_by(User.referral_count.desc())
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(r[0], r[1] or "Anonim", r[2]) for r in rows]


# ============== PROMO CODES ==============

class PromoCodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, code: str) -> Optional[PromoCode]:
        stmt = select(PromoCode).where(PromoCode.code == code.upper())
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(
        self,
        code: str,
        discount_percent: int,
        max_uses: int = 100,
        bonus_days: int = 0,
        valid_until: Optional[datetime] = None,
        created_by: Optional[int] = None,
    ) -> PromoCode:
        promo = PromoCode(
            code=code.upper(),
            discount_percent=discount_percent,
            max_uses=max_uses,
            bonus_days=bonus_days,
            valid_until=valid_until,
            created_by=created_by,
        )
        self.session.add(promo)
        await self.session.flush()
        return promo

    async def use(self, promo: PromoCode) -> bool:
        if not promo.is_active:
            return False
        if promo.valid_until and datetime.utcnow() > promo.valid_until:
            return False
        if promo.times_used >= promo.max_uses:
            return False
        promo.times_used += 1
        await self.session.flush()
        return True

    async def list_active(self) -> Sequence[PromoCode]:
        stmt = select(PromoCode).where(PromoCode.is_active == True)  # noqa: E712
        return (await self.session.execute(stmt)).scalars().all()


# ============== AUDIT LOG ==============

class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        event: str,
        actor_id: Optional[int] = None,
        target_id: Optional[int] = None,
        payload: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            event=event,
            actor_id=actor_id,
            target_id=target_id,
            payload=payload or {},
            ip_address=ip_address,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def recent(self, limit: int = 100) -> Sequence[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()


# ============== BROADCASTS ==============

class BroadcastRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        text: str,
        created_by: int,
        media_path: Optional[str] = None,
        target_tier: Optional[int] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> Broadcast:
        bc = Broadcast(
            text=text,
            media_path=media_path,
            target_tier=target_tier,
            scheduled_at=scheduled_at,
            created_by=created_by,
            status="scheduled" if scheduled_at else "draft",
        )
        self.session.add(bc)
        await self.session.flush()
        return bc

    async def list_scheduled(self) -> Sequence[Broadcast]:
        stmt = select(Broadcast).where(Broadcast.status == "scheduled")
        return (await self.session.execute(stmt)).scalars().all()


# ============== PRESETS ==============

class PresetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: int, name: str, tool: ImageTool, params: dict) -> ImagePreset:
        p = ImagePreset(user_id=user_id, name=name, tool=tool.value, params=params)
        self.session.add(p)
        await self.session.flush()
        return p

    async def user_presets(self, user_id: int) -> Sequence[ImagePreset]:
        stmt = select(ImagePreset).where(ImagePreset.user_id == user_id).order_by(ImagePreset.use_count.desc())
        return (await self.session.execute(stmt)).scalars().all()


# ============== STATS ==============

class StatsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure(self) -> GlobalStat:
        stat = await self.session.get(GlobalStat, 1)
        if stat is None:
            stat = GlobalStat(id=1)
            self.session.add(stat)
            await self.session.flush()
        return stat

    async def snapshot(self) -> dict:
        stat = await self.ensure()
        return {
            "total_users": stat.total_users,
            "total_premium": stat.total_premium,
            "total_processed": stat.total_processed,
            "total_revenue": stat.total_revenue,
        }


__all__ = [
    "UserRepository",
    "ImageJobRepository",
    "PaymentRepository",
    "SubscriptionRepository",
    "ReferralRepository",
    "PromoCodeRepository",
    "AuditRepository",
    "BroadcastRepository",
    "PresetRepository",
    "StatsRepository",
]