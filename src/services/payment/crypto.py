"""Crypto payment provider (NOWPayments / Coinbase Commerce)."""
from __future__ import annotations

import logging

import aiohttp

from src.config.settings import settings
from src.services.payment.base import PaymentProvider, PaymentResult

logger = logging.getLogger(__name__)


class CryptoProvider(PaymentProvider):
    name = "crypto"

    async def create(self, user_id: int, plan_code: str, amount: float, currency: str) -> PaymentResult:
        api_key = settings.NOWPAYMENTS_API_KEY
        if not api_key:
            return PaymentResult(False, 0, amount, currency, {}, "Crypto not configured")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.nowpayments.io/v1/payment",
                    json={
                        "price_amount": amount,
                        "price_currency": currency.lower(),
                        "pay_currency": "usdttrc20",
                        "order_id": f"{user_id}_{plan_code}",
                        "order_description": f"Premium {plan_code}",
                    },
                    headers={"x-api-key": api_key},
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        return PaymentResult(
                            success=True,
                            payment_id=0,
                            amount=amount,
                            currency=currency,
                            payload={"pay_url": data.get("invoice_url"), "external_id": str(data.get("payment_id"))},
                        )
                    return PaymentResult(False, 0, amount, currency, {}, str(data))
        except Exception as e:
            logger.exception("Crypto error: %s", e)
            return PaymentResult(False, 0, amount, currency, {}, str(e))

    async def check(self, payment_id: int) -> PaymentResult:
        return PaymentResult(True, payment_id, 0, "", {}, "manual_check")

    async def handle_webhook(self, data: dict) -> PaymentResult:
        try:
            if data.get("payment_status") in ("finished", "confirmed"):
                ext_id = str(data.get("payment_id"))
                return PaymentResult(True, 0, 0, "", {"external_id": ext_id, "completed": True}, "ok")
        except Exception as e:
            logger.exception("Crypto webhook error: %s", e)
        return PaymentResult(False, 0, 0, "", {}, "invalid")


__all__ = ["CryptoProvider"]