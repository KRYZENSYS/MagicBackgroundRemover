"""User repository — async CRUD operations."""
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, ProcessedImage, Payment
from core.settings import settings


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create(self, telegram_id: int, **kwargs) -> tuple[User, bool]:
        user = await self.get(telegram_id)
        if user:
            return user, False
        user = await self.create(telegram_id=telegram_id, **kwargs)
        return user, True

    async def update(self, telegram_id: int, **fields) -> None:
        await self.session.execute(update(User).where(User.telegram_id == telegram_id).values(**fields))
        await self.session.commit()

    async def increment_processed(self, telegram_id: int) -> None:
        today = datetime.utcnow().date()
        user = await self.get(telegram_id)
        if not user:
            return
        if user.last_process_date and user.last_process_date.date() == today:
            user.daily_processed += 1
        else:
            user.daily_processed = 1
        user.last_process_date = datetime.utcnow()
        user.total_processed += 1
        user.last_active = datetime.utcnow()
        await self.session.commit()

    async def check_daily_limit(self, telegram_id: int) -> bool:
        """Returns True if user has remaining quota."""
        user = await self.get(telegram_id)
        if not user:
            return True
        if user.banned:
            return False
        if user.premium and user.premium_until and user.premium_until > datetime.utcnow():
            return user.daily_processed < settings.PREMIUM_DAILY_LIMIT
        if user.trial_used and not user.premium:
            return user.daily_processed < settings.FREE_DAILY_LIMIT
        return True

    async def ban(self, telegram_id: int, reason: str = "") -> None:
        await self.update(telegram_id, banned=True, ban_reason=reason)

    async def unban(self, telegram_id: int) -> None:
        await self.update(telegram_id, banned=False, ban_reason=None)

    async def set_premium(self, telegram_id: int, days: int) -> None:
        until = datetime.utcnow() + timedelta(days=days)
        await self.update(telegram_id, premium=True, premium_until=until)

    async def set_language(self, telegram_id: int, lang: str) -> None:
        await self.update(telegram_id, language=lang)

    async def list_all(self, offset: int = 0, limit: int = 100) -> List[User]:
        result = await self.session.execute(select(User).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def count_active(self, days: int = 7) -> int:
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(select(func.count(User.id)).where(User.last_active > since))
        return result.scalar_one()

    async def count_premium(self) -> int:
        result = await self.session.execute(select(func.count(User.id)).where(User.premium == True))
        return result.scalar_one()

    async def count_today(self) -> int:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(select(func.count(User.id)).where(User.join_date >= today_start))
        return result.scalar_one()

    async def top_referrers(self, limit: int = 10) -> List[User]:
        result = await self.session.execute(
            select(User).order_by(User.referral_count.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def search(self, query: str, limit: int = 20) -> List[User]:
        like = f"%{query}%"
        result = await self.session.execute(
            select(User).where(
                (User.username.ilike(like)) | (User.first_name.ilike(like)) | (User.telegram_id == int(query) if query.isdigit() else False)
            ).limit(limit)
        )
        return list(result.scalars().all())