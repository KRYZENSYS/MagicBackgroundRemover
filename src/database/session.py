"""Async database engine and session factory."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config.logging import logger
from src.config.settings import settings
from src.database.models import Base


def _create_engine() -> AsyncEngine:
    """Build the async SQLAlchemy engine.

    Works for SQLite (aiosqlite), PostgreSQL (asyncpg) and MySQL (aiomysql) by
    inferring from the DATABASE_URL scheme.
    """
    connect_args: dict = {}
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_async_engine(
        url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine: AsyncEngine = _create_engine()
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def init_db() -> None:
    """Create all tables. Idempotent."""
    # Ensure parent directories exist for SQLite file path
    if settings.DATABASE_URL.startswith("sqlite"):
        from urllib.parse import urlparse

        path = urlparse(settings.DATABASE_URL).path.replace("sqlite+aiosqlite:///", "")
        if path and path != ":memory:":
            from pathlib import Path

            Path(path).parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready (%s)", settings.DATABASE_URL.split("://")[0])


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context-managed session (preferred)."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    await engine.dispose()


__all__ = ["engine", "async_session", "init_db", "get_session", "close_db"]