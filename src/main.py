"""Main entrypoint: starts bot (polling or webhook) and FastAPI (for webhooks)."""
from __future__ import annotations

import asyncio
import logging
import signal
import sys

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot import setup_bot
from src.config.logging import logger, setup_logging
from src.config.settings import settings
from src.database.session import init_db


async def on_startup(bot: Bot):
    logger.info("Bot startup...")
    await init_db()
    from src.services.notification.scheduler import init_scheduler
    scheduler = init_scheduler(bot)
    await scheduler.start()
    # Notify admins
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🟢 Bot ishga tushdi.")
        except Exception:
            pass


async def on_shutdown(bot: Bot):
    logger.info("Bot shutdown...")
    from src.services.notification.scheduler import notification_scheduler
    if notification_scheduler:
        await notification_scheduler.stop()
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🔴 Bot to'xtadi.")
        except Exception:
            pass


async def run_polling():
    bot, dp = await setup_bot()
    await on_startup(bot)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown(bot)


async def run_with_api():
    bot, dp = await setup_bot()
    await on_startup(bot)
    # Start FastAPI in parallel
    from src.api.app import create_app
    app = create_app()

    config = uvicorn.Config(
        app,
        host=settings.WEBHOOK_HOST,
        port=settings.WEBHOOK_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    api_task = asyncio.create_task(server.serve())

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        server.should_exit = True
        await api_task
        await on_shutdown(bot)


def main():
    setup_logging()
    if settings.USE_WEBHOOK:
        asyncio.run(run_with_api())
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()

__all__ = ["main"]