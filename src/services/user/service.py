"""User service: create, fetch, update, quota."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import FREE_DAILY_LIMIT, PREMIUM_DAILY_LIMIT
from src.database.models.user import User


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_or_create(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language: str = "uz",
        referred_by: int | None = None,
    ) -> tuple[User, bool]:
        user = await self.get(user_id)
        if user:
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if updated:
                await self.session.commit()
            return user, False
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            referred_by=referred_by,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user, True

    async def set_language(self, user_id: int, language: str) -> User:
        user = await self.get(user_id)
        if not user:
            raise ValueError("user not found")
        user.language = language
        await self.session.commit()
        return user

    async def is_premium(self, user_id: int) -> bool:
        user = await self.get(user_id)
        if not user:
            return False
        return bool(user.is_premium and user.premium_until and user.premium_until > datetime.utcnow())

    async def can_process(self, user_id: int) -> tuple[bool, dict]:
        """Check quota without mutating."""
        user = await self.get(user_id)
        if not user:
            return False, {"remaining": 0, "limit": 0, "is_premium": False, "error": "user_not_found"}
        premium = await self.is_premium(user_id)
        limit = PREMIUM_DAILY_LIMIT if premium else FREE_DAILY_LIMIT
        # Reset daily count if day changed
        if user.last_processed_at and user.last_processed_at.date() < datetime.utcnow().date():
            user.daily_processed = 0
            await self.session.commit()
        remaining = max(0, limit - user.daily_processed)
        return remaining > 0, {
            "remaining": remaining,
            "limit": limit,
            "is_premium": premium,
            "total": user.total_processed,
        }

    async def increment_usage(self, user_id: int, count: int = 1) -> User:
        user = await self.get(user_id)
        if not user:
            raise ValueError("user not found")
        if user.last_processed_at and user.last_processed_at.date() < datetime.utcnow().date():
            user.daily_processed = 0
        user.daily_processed += count
        user.total_processed += count
        user.last_processed_at = datetime.utcnow()
        await self.session.commit()
        return user

    async def increment_referral(self, user_id: int) -> None:
        user = await self.get(user_id)
        if not user:
            return
        user.referral_count += 1
        await self.session.commit()

    async def list_all(self, limit: int = 100) -> list[User]:
        result = await self.session.execute(select(User).order_by(User.id.desc()).limit(limit))
        return list(result.scalars())

    async def count(self) -> int:
        from sqlalchemy import func
        result = await self.session.execute(select(func.count()).select_from(User))
        return int(result.scalar() or 0)

    async def count_premium(self) -> int:
        from sqlalchemy import func, select
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.is_premium == True)
        )
        return int(result.scalar() or 0)

    async def count_today(self) -> int:
        from sqlalchemy import func, select
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.created_at >= today_start)
        )
        return int(result.scalar() or 0)


__all__ = ["UserService"]