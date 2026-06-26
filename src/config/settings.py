"""Application settings loaded from .env / environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "MagicBackgroundRemover"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Telegram
    BOT_TOKEN: str = ""
    ADMIN_IDS: List[int] = Field(default_factory=list)
    ADMIN_TOKEN: str = ""

    # Webhook
    USE_WEBHOOK: bool = False
    WEBHOOK_BASE: str = "http://localhost:8080"
    WEBHOOK_URL: str = ""
    WEBHOOK_HOST: str = "0.0.0.0"
    WEBHOOK_PORT: int = 8080
    WEBHOOK_PATH: str = "/tg/webhook"
    SECRET_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/db.sqlite"
    USE_REDIS: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # Payments
    CLICK_MERCHANT_ID: str = ""
    CLICK_SERVICE_ID: str = ""
    CLICK_SECRET: str = ""
    PAYME_MERCHANT_ID: str = ""
    PAYME_KEY: str = ""
    PAYME_ENDPOINT: str = "https://checkout.paycom.uz"
    STRIPE_SECRET_KEY: str = ""
    NOWPAYMENTS_API_KEY: str = ""

    # AI / models
    MODELS_DIR: str = "/data/models"
    FORCE_CPU: bool = False

    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "hello@magicbg.bot"

    # Sentry
    SENTRY_DSN: str = ""

    # Limits
    FREE_DAILY_LIMIT: int = 5
    PREMIUM_DAILY_LIMIT: int = 1000

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def _parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        if isinstance(v, (list, tuple)):
            return [int(x) for x in v]
        return v or []

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ("production", "prod")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

__all__ = ["Settings", "get_settings", "settings"]