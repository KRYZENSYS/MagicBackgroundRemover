"""User account management: registration, profile, limits, ban."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import logger
from src.config.settings import settings
from src.constants import (
    FREE_DAILY_LIMIT,
    PREMIUM_DAILY_LIMIT,
    TRIAL_DURATION_DAYS,
    USER_LEVEL_ADMIN,
    USER_LEVEL_PREMIUM,
    USER_LEVEL_USER,
)
from src.database.models.user import User
from src.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        res = await self.session.execute(select(User).where(User.username == username.lstrip("@")))
        return res.scalar_one_or_none()

    async def get_or_create(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: str = "uz",
        referred_by: Optional[int] = None,
    ) -> tuple[User, bool]:
        user = await self.get(user_id)
        if user:
            return user, False
        user = User(
            id=user_id,
            username=(username or "").lstrip("@") or None,
            first_name=first_name,
            last_name=last_name,
            language=language,
            referred_by=referred_by,
            joined_at=datetime.utcnow(),
        )
        self.session.add(user)
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.exception("Failed to create user: %s", e)
            raise
        return user, True

    async def update_profile(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: Optional[str] = None,
    ) -> User:
        user = await self.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        if username is not None:
            user.username = username.lstrip("@") or None
        if first_name is not None:
            user.first_name = first_name[:64]
        if last_name is not None:
            user.last_name = last_name[:64]
        if language is not None:
            if language not in ("uz", "ru", "en"):
                raise ValidationError("Unsupported language")
            user.language = language
        user.updated_at = datetime.utcnow()
        await self.session.commit()
        return user

    async def set_premium(self, user_id: int, days: int) -> User:
        user = await self.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        now = datetime.utcnow()
        base = user.premium_until if (user.premium and user.premium_until and user.premium_until > now) else now
        user.premium_until = base + timedelta(days=days)
        user.is_premium = True
        user.updated_at = now
        await self.session.commit()
        return user

    async def remove_premium(self, user_id: int) -> User:
        user = await self.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        user.is_premium = False
        user.premium_until = None
        await self.session.commit()
        return user

    async def activate_trial(self, user_id: int) -> User:
        user = await self.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        if user.trial_used:
            raise ValidationError("Trial already used")
        user.trial_used = True
        user.is_premium = True
        user.premium_until = datetime.utcnow() + timedelta(days=TRIAL_DURATION_DAYS)
        await self.session.commit()
        return user

    async def can_process(self, user_id: int) -> tuple[bool, dict]:
        """Returns (allowed, info)."""
        user = await self.get(user_id)
        if not user:
            return True, {"reason": "new_user", "remaining": FREE_DAILY_LIMIT}
        if user.is_banned:
            return False, {"reason": "banned"}
        if user.is_admin:
            return True, {"reason": "admin", "remaining": -1}
        limit = PREMIUM_DAILY_LIMIT if (user.is_premium and user.premium_until and user.premium_until > datetime.utcnow()) else FREE_DAILY_LIMIT
        # Reset daily counter if a new day
        today = datetime.utcnow().date()
        if user.last_active_date != today:
            user.last_active_date = today
            user.daily_processed = 0
            await self.session.commit()
        remaining = max(0, limit - user.daily_processed)
        return remaining > 0, {"remaining": remaining, "limit": limit, "is_premium": user.is_premium}

    async def increment_usage(self, user_id: int, amount: int = 1) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                daily_processed=User.daily_processed + amount,
                total_processed=User.total_processed + amount,
                last_active_at=datetime.utcnow(),
            )
        )
        await self.session.commit()

    async def set_language(self, user_id: int, lang: str) -> None:
        if lang not in ("uz", "ru", "en"):
            raise ValidationError("Unsupported language")
        await self.session.execute(
            update(User).where(User.id == user_id).values(language=lang, updated_at=datetime.utcnow())
        )
        await self.session.commit()

    async def ban(self, user_id: int, reason: str = "") -> User:
        user = await self.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        if user.is_admin:
            raise PermissionDeniedError("Cannot ban admin")
        user.is_banned = True
        user.ban_reason = reason[:500]
        await self.session.commit()
        return user

    async def unban(self, user_id: int) -> User:
        user = await self.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        user.is_banned = False
        user.ban_reason = None
        await self.session.commit()
        return user

    async def warn(self, user_id: int, reason: str = "") -> User:
        user = await self.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        user.warn_count += 1
        if user.warn_count >= 3:
            user.is_banned = True
            user.ban_reason = f"Auto-ban after 3 warnings. Last reason: {reason[:200]}"
        await self.session.commit()
        return user

    async def list_admins(self) -> list[User]:
        res = await self.session.execute(select(User).where(User.is_admin == True))
        return list(res.scalars().all())

    async def list_premium(self) -> list[User]:
        res = await self.session.execute(
            select(User).where(User.is_premium == True, User.premium_until > datetime.utcnow())
        )
        return list(res.scalars().all())

    async def list_banned(self) -> list[User]:
        res = await self.session.execute(select(User).where(User.is_banned == True))
        return list(res.scalars().all())

    async def search(self, q: str, limit: int = 20) -> list[User]:
        like = f"%{q}%"
        res = await self.session.execute(
            select(User)
            .where(
                (User.username.ilike(like))
                | (User.first_name.ilike(like))
                | (User.last_name.ilike(like))
                | (User.id.cast(__import__("sqlalchemy").String).ilike(f"%{q}%"))
            )
            .limit(limit)
        )
        return list(res.scalars().all())

    async def stats(self) -> dict:
        total = await self.session.execute(select(func.count(User.id)))
        premium = await self.session.execute(
            select(func.count(User.id)).where(User.is_premium == True, User.premium_until > datetime.utcnow())
        )
        banned = await self.session.execute(select(func.count(User.id)).where(User.is_banned == True))
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_today = await self.session.execute(select(func.count(User.id)).where(User.joined_at >= today))
        active_week = await self.session.execute(
            select(func.count(User.id)).where(User.last_active_at >= datetime.utcnow() - timedelta(days=7))
        )
        return {
            "total": total.scalar_one(),
            "premium": premium.scalar_one(),
            "banned": banned.scalar_one(),
            "new_today": new_today.scalar_one(),
            "active_week": active_week.scalar_one(),
        }


# Note: user_service instance is created per-request with a session.
# The helpers below create short-lived sessions for top-level operations.
async def _with_user_service(callback):
    from src.database.session import async_session
    async with async_session() as s:
        return await callback(UserService(s))


user_service = None  # instantiated on-demand

__all__ = ["UserService", "user_service"]