"""Stripe payment provider (international)."""
from __future__ import annotations

import time

import aiohttp

from src.config.logging import logger
from src.config.settings import settings
from src.services.payment.provider import PaymentProvider, PaymentResult


class StripeProvider(PaymentProvider):
    name = "stripe"

    def __init__(self):
        self.secret = settings.STRIPE_SECRET_KEY

    async def create(self, user_id: int, amount: int, plan_code: str, **kwargs) -> PaymentResult:
        if not self.secret:
            return PaymentResult(success=False, error="Stripe credentials not set")
        order_id = f"stripe_{user_id}_{int(time.time())}"
        amount_cents = amount * 100
        url = "https://api.stripe.com/v1/checkout/sessions"
        headers = {"Authorization": f"Bearer {self.secret}"}
        form = {
            "payment_method_types[]": "card",
            "line_items[0][price_data][currency]": "usd",
            "line_items[0][price_data][unit_amount]": str(amount_cents),
            "line_items[0][price_data][product_data][name]": f"Premium {plan_code}",
            "line_items[0][quantity]": "1",
            "mode": "payment",
            "success_url": f"{settings.WEBHOOK_BASE}/payment/stripe/success?session_id={'{CHECKOUT_SESSION_ID}'}",
            "cancel_url": f"{settings.WEBHOOK_BASE}/payment/stripe/cancel",
            "metadata[order_id]": order_id,
            "metadata[user_id]": str(user_id),
            "metadata[plan_code]": plan_code,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=form, timeout=15) as resp:
                    data = await resp.json()
                    if resp.status in (200, 201):
                        return PaymentResult(
                            success=True,
                            payment_id=None,
                            amount=amount,
                            payload={"pay_url": data.get("url"), "session_id": data.get("id"), "order_id": order_id},
                        )
                    return PaymentResult(success=False, error=str(data))
        except Exception as e:
            logger.exception("Stripe create failed: %s", e)
            return PaymentResult(success=False, error=str(e))

    async def verify(self, payload: dict) -> bool:
        return bool(payload.get("stripe_signature"))

    async def handle_webhook(self, body: dict) -> dict:
        event_type = body.get("type")
        if event_type == "checkout.session.completed":
            return {"status": "completed", "session": body.get("data", {}).get("object", {}).get("id")}
        return {"status": "ignored"}


__all__ = ["StripeProvider"]