"""Main bot entry point."""
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.settings import settings
from core.logger import logger
from core.middleware import LoggingMiddleware, RateLimitMiddleware, AntiFloodMiddleware
from database.engine import init_db, close_db
from handlers import start, image, profile, premium, admin, referral


async def on_startup(bot: Bot):
    """Hook on bot startup."""
    await init_db()
    bot_info = await bot.get_me()
    logger.info(f"Bot started: @{bot_info.username}")


async def on_shutdown(bot: Bot):
    """Hook on bot shutdown."""
    await close_db()
    logger.info("Bot stopped")


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Middlewares
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(RateLimitMiddleware(rate=30, per=60))
    dp.message.middleware(AntiFloodMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(image.router)
    dp.include_router(profile.router)
    dp.include_router(premium.router)
    dp.include_router(admin.router)
    dp.include_router(referral.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting bot...")
    try:
        if settings.WEBHOOK_URL:
            from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
            from aiohttp import web
            app = web.Application()
            webhook_path = f"/webhook/{settings.BOT_TOKEN}"
            SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
            setup_application(app, dp, bot=bot)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, settings.API_HOST, settings.WEBHOOK_PORT)
            await site.start()
            await bot.set_webhook(f"{settings.WEBHOOK_URL}{webhook_path}")
            logger.info(f"Webhook running on port {settings.WEBHOOK_PORT}")
            await asyncio.Event().wait()
        else:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Fatal: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")