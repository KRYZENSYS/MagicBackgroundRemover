"""Click.uz payment provider (Uzbekistan)."""
from __future__ import annotations

import hashlib
import time
from typing import Optional

import aiohttp

from src.config.logging import logger
from src.config.settings import settings
from src.services.payment.provider import PaymentProvider, PaymentResult, PaymentStatus


class ClickProvider(PaymentProvider):
    code = "click"

    def __init__(self):
        self.merchant_id = settings.CLICK_MERCHANT_ID
        self.service_id = settings.CLICK_SERVICE_ID
        self.secret_key = settings.CLICK_SECRET_KEY

    def _sign(self, *args: str) -> str:
        s = "|".join(args)
        return hashlib.sha1(s.encode()).hexdigest()

    async def create_invoice(
        self,
        user_id: int,
        amount: float,
        description: str,
        payload: str = "",
        currency: str = "UZS",
    ) -> PaymentResult:
        if not self.merchant_id or not self.secret_key:
            return PaymentResult(False, PaymentStatus.FAILED, error="Click not configured")
        try:
            url = "https://api.click.uz/v2/merchant/invoice/create"
            ts = str(int(time.time()))
            sign = self._sign(ts, str(self.service_id or ""), payload, str(int(amount)))
            body = {
                "service_id": self.service_id,
                "merchant_id": self.merchant_id,
                "amount": float(amount),
                "transaction_param": payload,
                "merchant_trans_id": payload,
                "sign": sign,
                "sign_time": ts,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    data = await resp.json()
            if data.get("error_code") == 0:
                return PaymentResult(
                    success=True,
                    status=PaymentStatus.PENDING,
                    amount=float(amount),
                    currency=currency,
                    payload={"invoice_id": data.get("invoice_id"), "pay_url": data.get("pay_url")},
                )
            return PaymentResult(False, PaymentStatus.FAILED, error=str(data.get("error_note"))[:200])
        except Exception as e:
            logger.exception("Click create_invoice failed")
            return PaymentResult(False, PaymentStatus.FAILED, error=str(e)[:200])

    async def verify(self, transaction_id: str) -> PaymentResult:
        """Verification via Click Prepare/Complete webhooks (handled in handler)."""
        return PaymentResult(True, PaymentStatus.COMPLETED, transaction_id=transaction_id)


__all__ = ["ClickProvider"]