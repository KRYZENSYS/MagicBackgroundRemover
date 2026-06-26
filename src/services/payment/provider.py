"""Payment provider base abstraction."""
from __future__ import annotations

import abc
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


@dataclass
class PaymentResult:
    success: bool
    status: PaymentStatus
    transaction_id: Optional[str] = None
    amount: float = 0
    currency: str = "UZS"
    error: Optional[str] = None
    payload: Optional[dict] = None


class PaymentProvider(abc.ABC):
    code: str = "base"

    @abc.abstractmethod
    async def create_invoice(
        self,
        user_id: int,
        amount: float,
        description: str,
        payload: str = "",
        currency: str = "UZS",
    ) -> PaymentResult: ...

    @abc.abstractmethod
    async def verify(self, transaction_id: str) -> PaymentResult: ...

    async def refund(self, transaction_id: str, amount: Optional[float] = None) -> PaymentResult:
        return PaymentResult(False, PaymentStatus.FAILED, error="Refund not supported")