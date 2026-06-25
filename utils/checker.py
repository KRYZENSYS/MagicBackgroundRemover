"""Kanal obunasini tekshirish"""
from aiogram import Bot
from config import REQUIRED_CHANNELS
from utils.logger import logger


async def check_subscription(bot: Bot, user_id: int) -> bool:
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logger.error(f"Sub check {ch}: {e}")
            return False
    return True