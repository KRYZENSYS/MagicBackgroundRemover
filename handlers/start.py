"""Start and basic commands handler."""
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from core.logger import logger
from database.repositories.user_repo import UserRepository
from database.engine import async_session
from keyboards.inline import main_menu, language_select, subscription_required
from localization import get_text

router = Router()


@router.message(CommandStart(deep_link=False))
async def cmd_start(message: Message):
    async with async_session() as session:
        repo = UserRepository(session)
        args = message.text.split()
        invited_by = None
        if len(args) > 1 and args[1].startswith("ref_"):
            try:
                invited_by = int(args[1].replace("ref_", ""))
            except ValueError:
                pass
        user, created = await repo.get_or_create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            invited_by=invited_by,
        )
        if created:
            logger.info(f"New user: {user.telegram_id} (@{user.username})")
        await message.answer(
            get_text(user.language, "welcome", name=message.from_user.first_name or ""),
            reply_markup=main_menu(user),
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    async with async_session() as session:
        repo = UserRepository(session)
        user = await repo.get(message.from_user.id)
        lang = user.language if user else "uz"
    await message.answer(get_text(lang, "help"), reply_markup=main_menu(user))


@router.message(Command("language"))
@router.message(F.text.in_(["🌐 Til", "🌐 Язык", "🌐 Language"]))
async def cmd_language(message: Message):
    await message.answer("🌐 Tilni tanlang:", reply_markup=language_select())


@router.callback_query(F.data.startswith("lang_"))
async def callback_language(callback):
    lang = callback.data.split("_")[1]
    async with async_session() as session:
        repo = UserRepository(session)
        await repo.set_language(callback.from_user.id, lang)
        user = await repo.get(callback.from_user.id)
    await callback.message.edit_text(
        get_text(lang, "language_set"),
        reply_markup=main_menu(user),
    )
    await callback.answer()