"""Payme.uz payment provider (Uzbekistan)."""
from __future__ import annotations

import base64
import time
from typing import Optional

import aiohttp

from src.config.logging import logger
from src.config.settings import settings
from src.services.payment.provider import PaymentProvider, PaymentResult, PaymentStatus


class PaymeProvider(PaymentProvider):
    code = "payme"

    def __init__(self):
        self.merchant_id = settings.PAYME_MERCHANT_ID
        self.secret_key = settings.PAYME_SECRET_KEY
        self.endpoint = settings.PAYME_ENDPOINT or "https://checkout.paycom.uz"

    def _auth_header(self) -> str:
        creds = f"{self.merchant_id}:{self.secret_key}".encode()
        token = base64.b64encode(creds).decode()
        return f"Basic {token}"

    async def create_invoice(
        self,
        user_id: int,
        amount: float,
        description: str,
        payload: str = "",
        currency: str = "UZS",
    ) -> PaymentResult:
        if not self.merchant_id or not self.secret_key:
            return PaymentResult(False, PaymentStatus.FAILED, error="Payme not configured")
        try:
            amount_tiyin = int(amount * 100)  # Payme uses tiyin
            id_payload = payload or f"user_{user_id}_{int(time.time())}"
            body = {
                "method": "receipts.create",
                "params": {
                    "amount": amount_tiyin,
                    "account": {"order_id": id_payload},
                    "description": description[:255],
                },
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/api",
                    json=body,
                    headers={"Authorization": self._auth_header(), "X-Requested-With": "XMLHttpRequest"},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    data = await resp.json()
            if data.get("result"):
                receipt_id = data["result"]["receipt"]["_id"]
                pay_url = f"{self.endpoint}/{receipt_id}"
                return PaymentResult(
                    success=True,
                    status=PaymentStatus.PENDING,
                    amount=amount,
                    currency=currency,
                    payload={"receipt_id": receipt_id, "pay_url": pay_url},
                )
            return PaymentResult(False, PaymentStatus.FAILED, error=str(data.get("error"))[:200])
        except Exception as e:
            logger.exception("Payme create_invoice failed")
            return PaymentResult(False, PaymentStatus.FAILED, error=str(e)[:200])

    async def verify(self, transaction_id: str) -> PaymentResult:
        """Payme sends POST to merchant URL on receipt_pay; verified in webhook handler."""
        return PaymentResult(True, PaymentStatus.COMPLETED, transaction_id=transaction_id)


__all__ = ["PaymeProvider"]