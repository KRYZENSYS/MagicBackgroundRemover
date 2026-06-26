"""ORM models. Compatible with SQLite, PostgreSQL and MySQL."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="uz")
    photo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    plan_tier: Mapped[int] = mapped_column(Integer, default=0)
    subscription_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)

    balance: Mapped[float] = mapped_column(Float, default=0.0)

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_warned: Mapped[bool] = mapped_column(Boolean, default=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    ban_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    daily_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_paid: Mapped[float] = mapped_column(Float, default=0.0)

    referral_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    referred_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    referral_count: Mapped[int] = mapped_column(Integer, default=0)
    referral_earnings: Mapped[float] = mapped_column(Float, default=0.0)

    preferences: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    favorite_tools: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    join_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    jobs: Mapped[list["ImageJob"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def is_premium(self) -> bool:
        if self.plan_tier >= 2:
            if self.subscription_until is None:
                return self.plan_tier >= 3  # lifetime VIP
            return datetime.utcnow() < self.subscription_until
        return False

    @property
    def display_name(self) -> str:
        return self.first_name or self.username or f"User{self.telegram_id}"


class ImageJob(Base):
    __tablename__ = "image_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tool: Mapped[str] = mapped_column(String(64), index=True)
    input_file_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    output_file_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    input_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    output_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    params: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    file_size_in: Mapped[int] = mapped_column(Integer, default=0)
    file_size_out: Mapped[int] = mapped_column(Integer, default=0)
    is_batch: Mapped[bool] = mapped_column(Boolean, default=False)
    batch_size: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    user: Mapped["User"] = relationship(back_populates="jobs")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, index=True)
    plan: Mapped[str] = mapped_column(String(32))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    promo_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="payments")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(32))
    payment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="subscriptions")


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (UniqueConstraint("referrer_id", "referred_id", name="uq_referral_pair"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    referred_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    reward_given: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_days: Mapped[int] = mapped_column(Integer, default=0)
    reward_percent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    discount_percent: Mapped[int] = mapped_column(Integer)
    max_uses: Mapped[int] = mapped_column(Integer, default=100)
    times_used: Mapped[int] = mapped_column(Integer, default=0)
    bonus_days: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(64), index=True)
    actor_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    media_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    target_tier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    created_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ImagePreset(Base):
    __tablename__ = "image_presets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    tool: Mapped[str] = mapped_column(String(64))
    params: Mapped[dict] = mapped_column(JSON)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class GlobalStat(Base):
    """Single-row table for aggregate counters."""

    __tablename__ = "global_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    total_premium: Mapped[int] = mapped_column(Integer, default=0)
    total_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


__all__ = [
    "Base",
    "User",
    "ImageJob",
    "Payment",
    "Subscription",
    "Referral",
    "PromoCode",
    "AuditLog",
    "Broadcast",
    "ImagePreset",
    "GlobalStat",
]