"""Click.uz payment provider (Uzbekistan)."""
from __future__ import annotations

import hashlib
import logging
import time
from urllib.parse import urlencode

import aiohttp

from src.config.settings import settings
from src.services.payment.base import PaymentProvider, PaymentResult

logger = logging.getLogger(__name__)


class ClickProvider(PaymentProvider):
    name = "click"

    def __init__(self):
        self.merchant_id = settings.CLICK_MERCHANT_ID
        self.service_id = settings.CLICK_SERVICE_ID
        self.secret_key = settings.CLICK_SECRET_KEY

    async def create(self, user_id: int, plan_code: str, amount: float, currency: str) -> PaymentResult:
        if not self.merchant_id:
            return PaymentResult(False, 0, amount, currency, {}, "Click not configured")
        # Generate an external id for tracking
        ext_id = f"{user_id}_{int(time.time())}"
        params = {
            "merchant_id": self.merchant_id,
            "service_id": self.service_id,
            "amount": f"{amount:.2f}",
            "transaction_param": ext_id,
            "return_url": settings.CLICK_RETURN_URL,
        }
        url = "https://my.click.uz/pay?" + urlencode(params)
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
        # Click sends click_trans_id + service_id + secret_key hash for verification
        try:
            sign_string = f"{data.get('click_trans_id')}{data.get('service_id')}{self.secret_key}{data.get('merchant_trans_id')}"
            expected = hashlib.md5(sign_string.encode()).hexdigest()
            if data.get("sign_string") != expected:
                return PaymentResult(False, 0, 0, "", {}, "invalid_signature")
            action = data.get("action")
            if action == "1":  # prepare
                return PaymentResult(True, int(data.get("merchant_trans_id", 0)), 0, "", {"action": "prepare"}, "ok")
            if action == "0":  # complete
                return PaymentResult(True, int(data.get("merchant_trans_id", 0)), 0, "", {"action": "complete"}, "ok")
        except Exception as e:
            logger.exception("Click webhook error: %s", e)
        return PaymentResult(False, 0, 0, "", {}, "invalid")


__all__ = ["ClickProvider"]