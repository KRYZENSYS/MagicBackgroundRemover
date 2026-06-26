"""Telegram Stars payment provider (XTR currency)."""
from __future__ import annotations

import time

from src.services.payment.provider import PaymentProvider, PaymentResult


class StarsProvider(PaymentProvider):
    name = "stars"

    async def create(self, user_id: int, amount: int, plan_code: str, **kwargs) -> PaymentResult:
        # amount in Stars (1 Star ≈ $0.02)
        order_id = f"stars_{user_id}_{int(time.time())}"
        return PaymentResult(
            success=True,
            payment_id=None,
            amount=amount,
            payload={"order_id": order_id, "currency": "XTR"},
        )

    async def verify(self, payload: dict) -> bool:
        return bool(payload.get("telegram_payment_charge_id"))

    async def handle_webhook(self, body: dict) -> dict:
        return {"status": "completed", "verified": True}


__all__ = ["StarsProvider"]