"""Image processing handlers - core AI functionality."""
import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from core.logger import logger
from core.exceptions import LimitExceededError, ProcessingError
from database.engine import async_session
from database.repositories.user_repo import UserRepository
from database.repositories.image_repo import ImageRepository
from services.image_processor import ImageProcessor
from services.storage import storage
from keyboards.inline import image_tools, after_process
from localization import get_text

router = Router()


@router.message(F.photo)
async def handle_photo(message: Message):
    """Receive image and present tool menu."""
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get(message.from_user.id)
        if not user:
            await message.answer("/start bosing")
            return
        if not await user_repo.check_daily_limit(user.telegram_id):
            raise LimitExceededError("Daily limit reached")
        await user_repo.increment_processed(user.telegram_id)
    await message.answer(
        get_text(user.language, "choose_tool"),
        reply_markup=image_tools(),
    )


@router.callback_query(F.data.startswith("tool_"))
async def callback_tool(callback: CallbackQuery):
    tool = callback.data.replace("tool_", "")
    await callback.message.edit_text(
        f"\u2728 Tool: {tool}\n\nEndi rasmni yuboring.",
    )
    await callback.answer()


@router.callback_query(F.data == "menu_main")
async def callback_main(callback: CallbackQuery):
    async with async_session() as session:
        repo = UserRepository(session)
        user = await repo.get(callback.from_user.id)
    await callback.message.edit_text(
        get_text(user.language if user else "uz", "main_menu"),
        reply_markup=main_menu_keyboard(user),
    )
    await callback.answer()