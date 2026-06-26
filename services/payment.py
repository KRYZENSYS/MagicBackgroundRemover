"""Payment service abstraction with multiple providers."""
from typing import Optional, Dict, Any
from core.settings import settings
from core.logger import logger


class PaymentService:
    """Unified payment interface."""

    async def create_invoice(self, provider: str, amount: float, currency: str = "UZS",
                             description: str = "") -> Dict[str, Any]:
        if provider == "telegram_stars":
            return await self._create_stars(amount, description)
        elif provider == "click":
            return await self._create_click(amount, description)
        elif provider == "payme":
            return await self._create_payme(amount, description)
        elif provider == "stripe":
            return await self._create_stripe(amount, currency, description)
        elif provider == "crypto":
            return await self._create_crypto(amount, currency, description)
        raise ValueError(f"Unknown provider: {provider}")

    async def _create_stars(self, amount: float, description: str) -> Dict[str, Any]:
        """Telegram Stars invoice payload."""
        stars = max(1, int(amount))
        return {"provider": "telegram_stars", "amount": stars, "currency": "XTR", "description": description}

    async def _create_click(self, amount: float, description: str) -> Dict[str, Any]:
        if not settings.CLICK_MERCHANT_ID:
            raise ValueError("CLICK_MERCHANT_ID not set")
        return {"provider": "click", "amount": amount, "currency": "UZS",
                "merchant_id": settings.CLICK_MERCHANT_ID, "description": description}

    async def _create_payme(self, amount: float, description: str) -> Dict[str, Any]:
        if not settings.PAYME_MERCHANT_ID:
            raise ValueError("PAYME_MERCHANT_ID not set")
        return {"provider": "payme", "amount": amount * 100, "currency": "UZS",
                "merchant_id": settings.PAYME_MERCHANT_ID, "description": description}

    async def _create_stripe(self, amount: float, currency: str, description: str) -> Dict[str, Any]:
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY not set")
        # Real integration would call stripe API here
        return {"provider": "stripe", "amount": int(amount * 100),
                "currency": currency.upper(), "description": description,
                "checkout_url": f"https://checkout.stripe.com/c/pay/session_demo"}

    async def _create_crypto(self, amount: float, currency: str, description: str) -> Dict[str, Any]:
        if not settings.CRYPTO_WALLET:
            raise ValueError("CRYPTO_WALLET not set")
        return {"provider": "crypto", "amount": amount, "currency": currency.upper(),
                "wallet": settings.CRYPTO_WALLET, "description": description}

    async def verify(self, provider: str, transaction_id: str) -> bool:
        """Verify transaction (mock)."""
        logger.info(f"Verifying {provider} tx: {transaction_id}")
        return True