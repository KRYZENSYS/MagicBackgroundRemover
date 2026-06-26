"""Telegram Stars payment provider (handled via Bot API)."""
from __future__ import annotations

import logging

from src.services.payment.base import PaymentProvider, PaymentResult

logger = logging.getLogger(__name__)


class TelegramStarsProvider(PaymentProvider):
    """Telegram Stars — invoices are sent via bot.send_invoice. We just return amount in XTR."""

    name = "stars"

    async def create(self, user_id: int, plan_code: str, amount: float, currency: str) -> PaymentResult:
        # amount is in UZS, convert to stars (1 star ≈ 100 UZS roughly, configurable)
        rate = 100  # 1 XTR ≈ 100 UZS
        stars = max(1, int(amount / rate))
        return PaymentResult(
            success=True,
            payment_id=0,
            amount=stars,
            currency="XTR",
            payload={"stars": stars, "plan_code": plan_code, "user_id": user_id},
        )

    async def check(self, payment_id: int) -> PaymentResult:
        return PaymentResult(True, payment_id, 0, "XTR", {}, "manual_check")

    async def handle_webhook(self, data: dict) -> PaymentResult:
        # Telegram Stars: pre_checkout_query + successful_payment update
        try:
            if "successful_payment" in data:
                payload = data.get("successful_payment", {})
                return PaymentResult(
                    True,
                    0,
                    int(payload.get("total_amount", 0)),
                    "XTR",
                    {"telegram_payment_charge_id": payload.get("telegram_payment_charge_id")},
                    "ok",
                )
        except Exception as e:
            logger.exception("Stars webhook error: %s", e)
        return PaymentResult(False, 0, 0, "", {}, "invalid")


__all__ = ["TelegramStarsProvider"]