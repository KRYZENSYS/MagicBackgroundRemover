"""Bot package: dispatcher + setup helper."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.middlewares import DatabaseMiddleware, I18nMiddleware, ThrottlingMiddleware, UserMiddleware
from src.bot.routers import (
    admin_router,
    ai_tools_router,
    image_router,
    language_router,
    premium_router,
    promo_router,
    referral_router,
    settings_router,
    start_router,
    support_router,
)
from src.config.settings import settings


def setup_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    # Middleware order matters
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate=1.0))

    dp.include_router(start_router)
    dp.include_router(settings_router)
    dp.include_router(language_router)
    dp.include_router(image_router)
    dp.include_router(ai_tools_router)
    dp.include_router(premium_router)
    dp.include_router(referral_router)
    dp.include_router(promo_router)
    dp.include_router(support_router)
    dp.include_router(admin_router)
    return dp


async def setup_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = setup_dispatcher()
    return bot, dp


__all__ = ["setup_bot", "setup_dispatcher"]