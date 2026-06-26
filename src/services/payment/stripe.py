"""Stripe payment provider."""
from __future__ import annotations

import logging
import time

import stripe

from src.config.settings import settings
from src.services.payment.base import PaymentProvider, PaymentResult

logger = logging.getLogger(__name__)


class StripeProvider(PaymentProvider):
    name = "stripe"

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    async def create(self, user_id: int, plan_code: str, amount: float, currency: str) -> PaymentResult:
        if not stripe.api_key:
            return PaymentResult(False, 0, amount, currency, {}, "Stripe not configured")
        try:
            # amount in smallest currency unit (cents)
            amount_cents = int(amount * 100)
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {"name": f"Premium {plan_code}"},
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=settings.STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.STRIPE_CANCEL_URL,
                metadata={"user_id": str(user_id), "plan_code": plan_code},
            )
            return PaymentResult(
                success=True,
                payment_id=0,
                amount=amount,
                currency=currency,
                payload={"pay_url": session.url, "external_id": session.id, "session_id": session.id},
            )
        except Exception as e:
            logger.exception("Stripe create error: %s", e)
            return PaymentResult(False, 0, amount, currency, {}, str(e))

    async def check(self, payment_id: int) -> PaymentResult:
        return PaymentResult(True, payment_id, 0, "", {}, "manual_check")

    async def handle_webhook(self, data: dict) -> PaymentResult:
        try:
            event_type = data.get("type")
            if event_type == "checkout.session.completed":
                obj = data.get("data", {}).get("object", {})
                ext_id = obj.get("id")
                return PaymentResult(True, 0, 0, "", {"external_id": ext_id, "completed": True}, "ok")
        except Exception as e:
            logger.exception("Stripe webhook error: %s", e)
        return PaymentResult(False, 0, 0, "", {}, "invalid")


__all__ = ["StripeProvider"]