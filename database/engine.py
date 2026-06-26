"""Async SQLAlchemy engine supporting SQLite/PostgreSQL/MySQL."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.settings import settings
from core.logger import logger


class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


# Engine factory
_engine_kwargs = {"echo": settings.DEBUG}
if "sqlite" in settings.DATABASE_URL:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_pre_ping": True,
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create tables."""
    from database.models import User, ProcessedImage, Payment, PromoCode, Broadcast, AuditLog, Plan, Subscription  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def close_db() -> None:
    await engine.dispose()
    logger.info("Database closed")