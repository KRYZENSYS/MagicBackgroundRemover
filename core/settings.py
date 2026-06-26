"""Production settings with Pydantic."""
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Bot
    BOT_TOKEN: str = "YOUR_BOT_TOKEN"
    BOT_USERNAME: str = "MagicBgBot"
    ADMIN_IDS: List[int] = Field(default_factory=list)
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PORT: int = 8080

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///database/bot.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Cache
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: str = Field(default="change-me")
    API_CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # Storage
    STORAGE_PATH: str = "storage/"
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_FORMATS: List[str] = Field(default_factory=lambda: ["png", "jpg", "jpeg", "webp"])

    # Payments
    PAYMENT_PROVIDER_TOKEN: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    CLICK_MERCHANT_ID: Optional[str] = None
    PAYME_MERCHANT_ID: Optional[str] = None
    CRYPTO_WALLET: Optional[str] = None

    # Plans
    PLAN_MONTHLY_PRICE: float = 50.0
    PLAN_YEARLY_PRICE: float = 500.0
    PLAN_LIFETIME_PRICE: float = 1999.0
    CURRENCY: str = "UZS"

    # Limits
    FREE_DAILY_LIMIT: int = 5
    PREMIUM_DAILY_LIMIT: int = 500
    TRIAL_DAYS: int = 3

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 9090

    # Environment
    ENV: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "UTC"

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admins(cls, v):
        if isinstance(v, str):
            return [int(x) for x in v.split(",") if x.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()