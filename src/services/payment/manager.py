"""Payment manager: routes to provider, persists Payment record."""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import logger
from src.database.models.payment import Payment
from src.database.session import async_session
from src.services.payment.base import PaymentProvider, PaymentResult
from src.services.payment.click import ClickProvider
from src.services.payment.payme import PaymeProvider
from src.services.payment.stripe import StripeProvider
from src.services.payment.stars import TelegramStarsProvider
from src.services.payment.crypto import CryptoProvider
from src.services.user.subscription import SubscriptionService


class PaymentManager:
    def __init__(self):
        self.providers: dict[str, PaymentProvider] = {
            "click": ClickProvider(),
            "payme": PaymeProvider(),
            "stripe": StripeProvider(),
            "stars": TelegramStarsProvider(),
            "crypto": CryptoProvider(),
        }

    def get(self, name: str) -> Optional[PaymentProvider]:
        return self.providers.get(name)

    async def create(self, user_id: int, plan_code: str, provider_name: str) -> tuple[PaymentResult, Optional[Payment]]:
        provider = self.get(provider_name)
        if not provider:
            return PaymentResult(False, 0, 0, "", {}, "Unknown provider"), None
        async with async_session() as session:
            sub_svc = SubscriptionService(session)
            plan = await sub_svc.get_plan(plan_code)
            if not plan:
                return PaymentResult(False, 0, 0, "", {}, "Plan not found"), None
            payment = Payment(
                user_id=user_id,
                plan_code=plan_code,
                provider=provider_name,
                amount=plan.price,
                currency=plan.currency,
                status="pending",
            )
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            result = await provider.create(user_id, plan_code, plan.price, plan.currency)
            payment.external_id = str(result.payload.get("external_id", ""))
            payment.payload = result.payload
            await session.commit()
            return result, payment

    async def confirm(self, payment_id: int) -> Optional[Payment]:
        """Mark payment as completed and grant premium."""
        async with async_session() as session:
            payment = await session.get(Payment, payment_id)
            if not payment or payment.status == "completed":
                return payment
            payment.status = "completed"
            payment.completed_at = __import__("datetime").datetime.utcnow()
            sub_svc = SubscriptionService(session)
            plan = await sub_svc.get_plan(payment.plan_code)
            days = plan.duration_days if plan else 30
            await sub_svc.grant_premium(payment.user_id, days, payment.plan_code)
            await session.commit()
            await session.refresh(payment)
            logger.info("Payment %s confirmed, premium granted to user %s for %s days", payment_id, payment.user_id, days)
            return payment

    async def fail(self, payment_id: int, reason: str = "") -> Optional[Payment]:
        async with async_session() as session:
            payment = await session.get(Payment, payment_id)
            if not payment:
                return None
            payment.status = "failed"
            payment.error_reason = reason
            await session.commit()
            return payment


payment_manager = PaymentManager()

__all__ = ["PaymentManager", "payment_manager", "PaymentResult"]