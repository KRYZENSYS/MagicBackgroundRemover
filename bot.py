"""MagicBackground Remover - Asosiy bot"""
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, BOT_NAME, BOT_VERSION
from database.models import init_db
from handlers import start, photo, referral, premium, admin
from utils.logger import logger


async def main():
    logger.info(f"{BOT_NAME} v{BOT_VERSION} ishga tushmoqda...")
    await init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(photo.router)
    dp.include_router(referral.router)
    dp.include_router(premium.router)
    dp.include_router(admin.router)
    logger.info("Bot tayyor!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")