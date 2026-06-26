"""Payment manager - routes to the correct provider and records transactions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from aiogram import Bot

from src.config.logging import logger
from src.database.models.payment import Payment
from src.database.session import async_session
from src.services.payment.click_provider import ClickProvider
from src.services.payment.payme_provider import PaymeProvider
from src.services.payment.provider import PaymentProvider, PaymentResult, PaymentStatus
from src.services.payment.telegram_stars import TelegramStarsProvider


class PaymentManager:
    """Routes payments to providers and persists them."""

    def __init__(self, bot: Bot | None = None):
        self._providers: dict[str, PaymentProvider] = {}
        if bot:
            self._providers["telegram_stars"] = TelegramStarsProvider(bot)
        self._providers["click"] = ClickProvider()
        self._providers["payme"] = PaymeProvider()

    def get(self, code: str) -> Optional[PaymentProvider]:
        return self._providers.get(code)

    async def create(
        self,
        user_id: int,
        plan_code: str,
        provider_code: str = "telegram_stars",
    ) -> tuple[PaymentResult, Optional[Payment]]:
        provider = self.get(provider_code)
        if not provider:
            return PaymentResult(False, PaymentStatus.FAILED, error=f"Unknown provider {provider_code}"), None
        # Get plan amount
        from src.services.user.subscription import SubscriptionService

        async with async_session() as s:
            svc = SubscriptionService(s)
            plan = await svc.get_plan(plan_code)
            description = f"{plan.name} subscription ({plan.duration_days} days)"
            amount = plan.price

            result = await provider.create_invoice(
                user_id=user_id,
                amount=amount,
                description=description,
                payload=f"{user_id}:{plan_code}",
                currency=plan.currency,
            )

            payment: Optional[Payment] = None
            if result.success:
                payment = Payment(
                    user_id=user_id,
                    plan_id=plan.id,
                    amount=amount,
                    currency=plan.currency,
                    provider=provider_code,
                    status=PaymentStatus.PENDING.value,
                    external_id=result.payload.get("invoice_id") or result.payload.get("receipt_id") if result.payload else None,
                    payload=result.payload or {},
                    created_at=datetime.utcnow(),
                )
                s.add(payment)
                await s.commit()
                await s.refresh(payment)
                # Attach payment id to result for traceability
                if result.payload is None:
                    result.payload = {}
                result.payload["payment_id"] = payment.id
            return result, payment

    async def mark_completed(self, payment_id: int, external_id: Optional[str] = None) -> Optional[Payment]:
        async with async_session() as s:
            payment = await s.get(Payment, payment_id)
            if not payment:
                return None
            payment.status = PaymentStatus.COMPLETED.value
            payment.completed_at = datetime.utcnow()
            if external_id:
                payment.external_id = external_id
            await s.commit()
            # Activate subscription
            from src.database.models.user import User
            from src.services.user.subscription import SubscriptionService

            user = await s.get(User, payment.user_id)
            sub_svc = SubscriptionService(s)
            await sub_svc.subscribe(user_id=payment.user_id, plan_code=payment.plan.code if payment.plan else "", payment_id=payment.id)
            return payment

    async def mark_failed(self, payment_id: int, reason: str = "") -> None:
        async with async_session() as s:
            payment = await s.get(Payment, payment_id)
            if not payment:
                return
            payment.status = PaymentStatus.FAILED.value
            payment.payload = {**(payment.payload or {}), "error": reason[:500]}
            await s.commit()

    async def refund(self, payment_id: int) -> bool:
        async with async_session() as s:
            payment = await s.get(Payment, payment_id)
            if not payment or payment.status != PaymentStatus.COMPLETED.value:
                return False
            provider = self.get(payment.provider)
            if not provider:
                return False
            result = await provider.refund(payment.external_id or "")
            if result.success:
                payment.status = PaymentStatus.REFUNDED.value
                await s.commit()
            return result.success


payment_manager: PaymentManager | None = None


__all__ = ["PaymentManager", "payment_manager"]