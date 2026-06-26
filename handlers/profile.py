"""Profile, settings, stats handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database.engine import async_session
from database.repositories.user_repo import UserRepository
from database.repositories.image_repo import ImageRepository
from keyboards.inline import main_menu
from localization import get_text

router = Router()


@router.message(Command("profile"))
@router.message(F.text.in_(["👤 Profil", "👤 Профиль", "👤 Profile"]))
async def cmd_profile(message: Message):
    async with async_session() as session:
        user_repo = UserRepository(session)
        img_repo = ImageRepository(session)
        user = await user_repo.get(message.from_user.id)
        if not user:
            await message.answer("/start")
            return
        total = await img_repo.total_count()
        avg = await img_repo.avg_duration()
        text = get_text(
            user.language, "profile",
            name=user.first_name or "User",
            telegram_id=user.telegram_id,
            username=f"@{user.username}" if user.username else "—",
            joined=user.join_date.strftime("%Y-%m-%d"),
            language=user.language.upper(),
            total=user.total_processed,
            premium="✅" if user.premium else "❌",
            until=user.premium_until.strftime("%Y-%m-%d") if user.premium_until else "—",
            trial_used="✅" if user.trial_used else "❌",
            referrer=user.invited_by or "—",
            referral_count=user.referral_count,
        )
        await message.answer(text, reply_markup=main_menu(user))


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    async with async_session() as session:
        img_repo = ImageRepository(session)
        today = await img_repo.today_count()
        total = await img_repo.total_count()
        avg = await img_repo.avg_duration()
        dist = await img_repo.tool_distribution()
        dist_text = "\n".join(f"  • {k}: {v}" for k, v in sorted(dist.items(), key=lambda x: -x[1])[:10])
        await message.answer(
            f"\u26a1 Bot statistikasi:\n\n"
            f"\u2022 Bugun: {today}\n"
            f"\u2022 Jami: {total}\n"
            f"\u2022 O'rtacha vaqt: {int(avg)}ms\n\n"
            f"\ud83d\udcca Top tools:\n{dist_text or '—'}"
        )


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    async with async_session() as session:
        repo = UserRepository(session)
        user = await repo.get(message.from_user.id)
        lang = user.language if user else "uz"
    from keyboards.inline import settings_menu
    await message.answer(get_text(lang, "settings"), reply_markup=settings_menu())