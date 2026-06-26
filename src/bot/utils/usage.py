"""Quota helpers for image processing."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.constants import FREE_DAILY_LIMIT, PREMIUM_DAILY_LIMIT
from src.services.user.service import UserService


async def get_remaining_quota(session: AsyncSession, user_id: int) -> dict:
    svc = UserService(session)
    user = await svc.get(user_id)
    if not user:
        return {"remaining": FREE_DAILY_LIMIT, "limit": FREE_DAILY_LIMIT, "is_premium": False}
    is_premium = bool(user.is_premium and user.premium_until and user.premium_until > __import__("datetime").datetime.utcnow())
    limit = PREMIUM_DAILY_LIMIT if is_premium else FREE_DAILY_LIMIT
    return {
        "remaining": max(0, limit - user.daily_processed),
        "limit": limit,
        "is_premium": is_premium,
        "total": user.total_processed,
    }


async def check_and_increment_usage(session: AsyncSession, user_id: int) -> tuple[bool, dict]:
    """Check quota, and if allowed, increment usage atomically."""
    svc = UserService(session)
    can, info = await svc.can_process(user_id)
    if not can:
        return False, info
    await svc.increment_usage(user_id, 1)
    info["remaining"] = max(0, info.get("remaining", 0) - 1)
    return True, info


__all__ = ["check_and_increment_usage", "get_remaining_quota"]