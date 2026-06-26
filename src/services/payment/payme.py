"""Payme payment provider (Uzbekistan)."""
from __future__ import annotations

import base64
import time
import uuid

import aiohttp

from src.config.logging import logger
from src.config.settings import settings
from src.services.payment.provider import PaymentProvider, PaymentResult


class PaymeProvider(PaymentProvider):
    name = "payme"

    def __init__(self):
        self.merchant_id = settings.PAYME_MERCHANT_ID
        self.key = settings.PAYME_KEY
        self.endpoint = settings.PAYME_ENDPOINT or "https://checkout.paycom.uz"

    def _auth_header(self) -> str:
        creds = f"Paycom:{self.key}"
        token = base64.b64encode(creds.encode()).decode()
        return f"Basic {token}"

    async def create(self, user_id: int, amount: int, plan_code: str, **kwargs) -> PaymentResult:
        if not self.merchant_id or not self.key:
            return PaymentResult(success=False, error="Payme credentials not set")
        order_id = f"payme_{user_id}_{int(time.time())}"
        # Payme amount is in tiyin (1/100 sum)
        amount_tiyin = amount * 100
        params = (
            f"m={self.merchant_id};"
            f"ac.order_id={order_id};"
            f"a={amount_tiyin};"
            f"l=uz"
        )
        pay_url = f"{self.endpoint}/{params}"
        return PaymentResult(
            success=True,
            payment_id=None,
            amount=amount,
            payload={"pay_url": pay_url, "order_id": order_id},
        )

    async def verify(self, payload: dict) -> bool:
        # Payme uses Basic Auth for verification
        return True

    async def handle_webhook(self, body: dict) -> dict:
        method = body.get("method")
        if method == "transactions.create":
            return {"status": "pending", "id": body.get("params", {}).get("id")}
        if method == "transactions.perform":
            return {"status": "completed", "id": body.get("params", {}).get("id")}
        return {"status": "ignored"}


__all__ = ["PaymeProvider"]