"""Payment provider base class + manager."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from src.config.logging import logger
from src.database.models.payment import Payment
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class PaymentResult:
    success: bool
    payment_id: Optional[int] = None
    amount: int = 0
    currency: str = "UZS"
    error: Optional[str] = None
    payload: dict = field(default_factory=dict)


class PaymentProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def create(self, user_id: int, amount: int, plan_code: str, **kwargs) -> PaymentResult:
        ...

    @abstractmethod
    async def verify(self, payload: dict) -> bool:
        ...

    @abstractmethod
    async def handle_webhook(self, body: dict) -> dict:
        ...


class PaymentManager:
    """Routes a payment creation/verification to the right provider."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._providers: dict[str, PaymentProvider] = {}
        self._register()

    def _register(self):
        from src.services.payment.click import ClickProvider
        from src.services.payment.payme import PaymeProvider
        from src.services.payment.stars import StarsProvider
        from src.services.payment.stripe import StripeProvider
        from src.services.payment.crypto import CryptoProvider

        for cls in (ClickProvider, PaymeProvider, StarsProvider, StripeProvider, CryptoProvider):
            try:
                p = cls()
                self._providers[p.name] = p
            except Exception as e:
                logger.warning("Failed to register %s: %s", cls.__name__, e)

    def get(self, name: str) -> PaymentProvider | None:
        return self._providers.get(name)

    def list(self) -> list[str]:
        return list(self._providers.keys())

    async def create(self, user_id: int, plan_code: str, provider_name: str) -> tuple[PaymentResult, Optional[Payment]]:
        from src.services.user.subscription import SubscriptionService

        sub_svc = SubscriptionService(self.session)
        plan = await sub_svc.get_plan(plan_code)
        if not plan:
            return PaymentResult(success=False, error="Plan not found"), None
        provider = self.get(provider_name)
        if not provider:
            return PaymentResult(success=False, error=f"Provider {provider_name} not available"), None

        # Convert price to provider currency if needed
        amount = int(plan.price)
        currency = plan.currency or "UZS"

        # Create pending payment record
        payment = Payment(
            user_id=user_id,
            plan_code=plan_code,
            provider=provider_name,
            amount=amount,
            currency=currency,
            status="pending",
        )
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)

        result = await provider.create(user_id, amount, plan_code)
        if result.success:
            payment.provider_payment_id = result.payload.get("order_id") or result.payload.get("session_id")
            payment.payload = result.payload
            await self.session.commit()
            result.payment_id = payment.id
        else:
            payment.status = "failed"
            payment.error = result.error
            await self.session.commit()
        return result, payment

    async def confirm(self, payment_id: int, success: bool = True) -> Optional[Payment]:
        payment = await self.session.get(Payment, payment_id)
        if not payment:
            return None
        payment.status = "completed" if success else "failed"
        await self.session.commit()
        if success:
            from src.services.user.subscription import SubscriptionService
            sub_svc = SubscriptionService(self.session)
            await sub_svc.activate_by_plan(payment.user_id, payment.plan_code)
        return payment


def payment_manager(session: AsyncSession) -> PaymentManager:
    return PaymentManager(session)


__all__ = ["PaymentProvider", "PaymentResult", "PaymentManager", "payment_manager"]