"""Click payment provider (Uzbekistan)."""
from __future__ import annotations

import hashlib
import time

import aiohttp

from src.config.logging import logger
from src.config.settings import settings
from src.services.payment.provider import PaymentProvider, PaymentResult


class ClickProvider(PaymentProvider):
    name = "click"

    def __init__(self):
        self.merchant_id = settings.CLICK_MERCHANT_ID
        self.service_id = settings.CLICK_SERVICE_ID
        self.secret = settings.CLICK_SECRET

    def _sign(self, params: dict) -> str:
        s = "&".join(f"{k}={params[k]}" for k in sorted(params.keys()))
        return hashlib.sha256((s + self.secret).encode()).hexdigest()

    async def create(self, user_id: int, amount: int, plan_code: str, **kwargs) -> PaymentResult:
        if not self.merchant_id or not self.secret:
            return PaymentResult(success=False, error="Click credentials not set")
        order_id = f"click_{user_id}_{int(time.time())}"
        url = "https://api.click.uz/v2/merchant/invoice/create"
        payload = {
            "merchant_id": self.merchant_id,
            "service_id": self.service_id,
            "amount": amount,
            "order_id": order_id,
            "phone_number": kwargs.get("phone", ""),
            "return_url": f"{settings.WEBHOOK_BASE}/payment/click/callback",
        }
        payload["sign"] = self._sign(payload)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=15) as resp:
                    data = await resp.json()
                    if data.get("error_code") == 0:
                        return PaymentResult(
                            success=True,
                            payment_id=None,
                            amount=amount,
                            payload={"pay_url": data["invoice_url"], "order_id": order_id},
                        )
                    return PaymentResult(success=False, error=str(data))
        except Exception as e:
            logger.exception("Click create invoice failed: %s", e)
            return PaymentResult(success=False, error=str(e))

    async def verify(self, payload: dict) -> bool:
        sign = payload.pop("sign", None)
        if not sign:
            return False
        return sign == self._sign(payload)

    async def handle_webhook(self, body: dict) -> dict:
        ok = await self.verify(dict(body))
        return {"verified": ok, "status": "completed" if ok else "failed"}


__all__ = ["ClickProvider"]