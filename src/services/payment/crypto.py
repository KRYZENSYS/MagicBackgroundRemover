"""Crypto payment provider (NOWPayments / Coinbase Commerce)."""
from __future__ import annotations

import time

import aiohttp

from src.config.logging import logger
from src.config.settings import settings
from src.services.payment.provider import PaymentProvider, PaymentResult


class CryptoProvider(PaymentProvider):
    name = "crypto"

    def __init__(self):
        self.api_key = settings.NOWPAYMENTS_API_KEY
        self.endpoint = "https://api.nowpayments.io/v1"

    async def create(self, user_id: int, amount: int, plan_code: str, **kwargs) -> PaymentResult:
        if not self.api_key:
            return PaymentResult(success=False, error="Crypto credentials not set")
        order_id = f"crypto_{user_id}_{int(time.time())}"
        url = f"{self.endpoint}/payment"
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        body = {
            "price_amount": amount,
            "price_currency": "usd",
            "pay_currency": kwargs.get("currency", "btc"),
            "order_id": order_id,
            "order_description": f"Premium {plan_code}",
            "success_url": f"{settings.WEBHOOK_BASE}/payment/crypto/success",
            "cancel_url": f"{settings.WEBHOOK_BASE}/payment/crypto/cancel",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body, timeout=15) as resp:
                    data = await resp.json()
                    if resp.status == 201:
                        return PaymentResult(
                            success=True,
                            payment_id=None,
                            amount=amount,
                            payload={"pay_url": data.get("invoice_url"), "order_id": order_id},
                        )
                    return PaymentResult(success=False, error=str(data))
        except Exception as e:
            logger.exception("Crypto create failed: %s", e)
            return PaymentResult(success=False, error=str(e))

    async def verify(self, payload: dict) -> bool:
        sig = payload.get("x-nowpayments-signature")
        return bool(sig)

    async def handle_webhook(self, body: dict) -> dict:
        status = body.get("payment_status")
        return {"status": "completed" if status == "finished" else "pending"}


__all__ = ["CryptoProvider"]