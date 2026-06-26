"""Dispatcher setup with all routers and middlewares."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from src.config.logging import logger
from src.config.settings import settings
from src.bot.middlewares import (
    DbSessionMiddleware,
    UserMiddleware,
    ThrottlingMiddleware,
    BanCheckMiddleware,
    AnalyticsMiddleware,
)
from src.bot.routers import (
    start_router,
    menu_router,
    image_router,
    background_router,
    upscale_router,
    passport_router,
    effects_router,
    premium_router,
    settings_router,
    admin_router,
    referral_router,
    support_router,
    errors_router,
)


def build_dispatcher(bot: Bot) -> Dispatcher:
    if settings.USE_REDIS:
        storage = RedisStorage.from_url(settings.REDIS_URL)
    else:
        storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Outer middleware order: user -> db -> analytics -> ban -> throttling
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    dp.message.middleware(AnalyticsMiddleware())
    dp.callback_query.middleware(AnalyticsMiddleware())
    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate_limit_per_min=60))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit_per_min=120))

    # Routers in priority order
    dp.include_router(errors_router)
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(menu_router)
    dp.include_router(image_router)
    dp.include_router(background_router)
    dp.include_router(upscale_router)
    dp.include_router(passport_router)
    dp.include_router(effects_router)
    dp.include_router(premium_router)
    dp.include_router(settings_router)
    dp.include_router(referral_router)
    dp.include_router(support_router)

    logger.info("Dispatcher built with %d routers", 13)
    return dp


def setup_dispatcher(bot: Bot) -> Dispatcher:
    return build_dispatcher(bot)


__all__ = ["build_dispatcher", "setup_dispatcher"]