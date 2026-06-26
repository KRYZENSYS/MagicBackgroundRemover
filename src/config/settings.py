"""Centralized application settings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Bot
    BOT_TOKEN: str = "YOUR_BOT_TOKEN_HERE"
    BOT_USERNAME: str = "@MagicBgBot"
    BOT_NAME: str = "MagicBackground Remover Pro"

    # Admins
    ADMIN_IDS: list[int] = Field(default_factory=list)
    REQUIRED_CHANNELS: list[str] = Field(default_factory=list)

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/bot.db"
    DATABASE_BACKUP_DIR: Path = Path("./data/backups")

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: str = "CHANGE_ME"
    API_CORS_ORIGINS: str = "*"

    # Limits
    FREE_DAILY_LIMIT: int = 5
    PREMIUM_DAILY_LIMIT: int = 100
    VIP_DAILY_LIMIT: int = 1000
    TRIAL_DAYS: int = 3
    MAX_FILE_SIZE_MB: int = 20
    BATCH_MAX_FILES: int = 10

    # AI
    REMBG_MODEL: str = "u2net"
    UPSCALER_MODEL: str = "RealESRGAN_x4plus"
    ENABLE_GFPGAN: bool = True
    ENABLE_ENHANCEMENT: bool = True

    # Storage
    STORAGE_DIR: Path = Path("./storage")
    TEMP_DIR: Path = Path("./tmp")
    CACHE_DIR: Path = Path("./cache")
    CACHE_TTL: int = 3600
    LOG_DIR: Path = Path("./logs")

    # Payments
    ENABLE_STARS: bool = True
    ENABLE_CLICK: bool = False
    ENABLE_PAYME: bool = False
    ENABLE_STRIPE: bool = False
    ENABLE_PAYPAL: bool = False
    ENABLE_CRYPTO: bool = False
    CLICK_MERCHANT_ID: str = ""
    CLICK_SECRET_KEY: str = ""
    PAYME_MERCHANT_ID: str = ""
    PAYME_SECRET_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_SECRET: str = ""
    CRYPTO_WALLET_BTC: str = ""
    CRYPTO_WALLET_ETH: str = ""
    CRYPTO_WALLET_USDT: str = ""

    # Prices
    PRICE_MONTHLY_STARS: int = 500
    PRICE_YEARLY_STARS: int = 5000
    PRICE_LIFETIME_STARS: int = 15000
    PRICE_MONTHLY_USD: int = 499
    PRICE_YEARLY_USD: int = 4999
    PRICE_LIFETIME_USD: int = 14999

    # Referral
    REFERRAL_BONUS_FREE_DAYS: int = 3
    REFERRAL_BONUS_PREMIUM_PERCENT: int = 20

    # Monitoring
    SENTRY_DSN: str = ""

    @field_validator("ADMIN_IDS", "REQUIRED_CHANNELS", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            if not v:
                return []
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def _to_ints(cls, v):
        if isinstance(v, list):
            return [int(x) for x in v]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins(self) -> list[str]:
        if self.API_CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.API_CORS_ORIGINS.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()