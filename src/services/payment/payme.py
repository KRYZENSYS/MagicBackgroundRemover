"""Payme.uz payment provider."""
from __future__ import annotations

import base64
import logging
import time

from src.config.settings import settings
from src.services.payment.base import PaymentProvider, PaymentResult

logger = logging.getLogger(__name__)


class PaymeProvider(PaymentProvider):
    name = "payme"

    def __init__(self):
        self.merchant_id = settings.PAYME_MERCHANT_ID
        self.key = settings.PAYME_KEY

    async def create(self, user_id: int, plan_code: str, amount: float, currency: str) -> PaymentResult:
        if not self.merchant_id:
            return PaymentResult(False, 0, amount, currency, {}, "Payme not configured")
        # Payme expects amount in tiyin (1/100 UZS)
        amount_tiyin = int(amount * 100)
        ext_id = f"{user_id}_{int(time.time())}"
        # Construct base64 encoded params for checkout URL
        params = f"m={self.merchant_id};ac.user_id={user_id};a={amount_tiyin};c={ext_id}"
        b64 = base64.b64encode(params.encode()).decode()
        url = f"https://checkout.paycom.uz/{b64}"
        return PaymentResult(
            success=True,
            payment_id=0,
            amount=amount,
            currency=currency,
            payload={"pay_url": url, "external_id": ext_id},
        )

    async def check(self, payment_id: int) -> PaymentResult:
        return PaymentResult(True, payment_id, 0, "", {}, "manual_check")

    async def handle_webhook(self, data: dict) -> PaymentResult:
        try:
            method = data.get("method")
            params = data.get("params", {})
            if method == "transactions.create":
                ext_id = params.get("account", {}).get("order_id") or params.get("account", {}).get("user_id")
                return PaymentResult(True, 0, 0, "", {"method": method, "ext_id": ext_id}, "ok")
            if method == "transactions.perform":
                trans_id = params.get("id")
                return PaymentResult(True, 0, 0, "", {"method": method, "trans_id": trans_id}, "ok")
        except Exception as e:
            logger.exception("Payme webhook error: %s", e)
        return PaymentResult(False, 0, 0, "", {}, "invalid")


__all__ = ["PaymeProvider"]