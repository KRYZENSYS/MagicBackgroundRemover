"""Payment provider base interface."""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentResult:
    success: bool
    payment_id: int
    amount: float
    currency: str
    payload: dict
    error: Optional[str] = None


class PaymentProvider(abc.ABC):
    """Abstract payment provider."""

    name: str = "base"

    @abc.abstractmethod
    async def create(self, user_id: int, plan_code: str, amount: float, currency: str) -> PaymentResult:
        ...

    @abc.abstractmethod
    async def check(self, payment_id: int) -> PaymentResult:
        ...

    @abc.abstractmethod
    async def handle_webhook(self, data: dict) -> PaymentResult:
        ...


__all__ = ["PaymentResult", "PaymentProvider"]