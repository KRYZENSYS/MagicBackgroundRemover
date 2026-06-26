"""Telegram Stars payment provider."""
from __future__ import annotations

import hashlib
import secrets
from typing import Optional

from aiogram import Bot

from src.config.logging import logger
from src.services.payment.provider import PaymentProvider, PaymentResult, PaymentStatus


class TelegramStarsProvider(PaymentProvider):
    code = "telegram_stars"

    def __init__(self, bot: Bot):
        self.bot = bot

    async def create_invoice(
        self,
        user_id: int,
        amount: float,
        description: str,
        payload: str = "",
        currency: str = "XTR",
    ) -> PaymentResult:
        try:
            stars_amount = max(1, int(amount))
            link = await self.bot.create_invoice_link(
                title="Premium subscription",
                description=description[:255],
                payload=payload or secrets.token_urlsafe(16),
                provider_token="",
                currency="XTR",
                prices=[{"label": description[:32], "amount": stars_amount}],
            )
            return PaymentResult(
                success=True,
                status=PaymentStatus.PENDING,
                transaction_id=None,
                amount=float(stars_amount),
                currency="XTR",
                payload={"invoice_link": link},
            )
        except Exception as e:
            logger.exception("Telegram Stars invoice failed")
            return PaymentResult(False, PaymentStatus.FAILED, error=str(e)[:200])

    async def verify(self, transaction_id: str) -> PaymentResult:
        """Verification happens via Bot pre-checkout / successful-payment webhooks."""
        return PaymentResult(
            success=True,
            status=PaymentStatus.COMPLETED,
            transaction_id=transaction_id,
        )


__all__ = ["TelegramStarsProvider"]