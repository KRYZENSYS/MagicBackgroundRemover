"""Passport photo router (Uzbek, RU, EU, US sizes)."""
from __future__ import annotations

import io

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.keyboards.inline import get_passport_kb
from src.bot.states import PassportFlow
from src.bot.utils.usage import check_and_increment_usage
from src.services.ai.effects import effects_service
from src.services.analytics.analytics import AnalyticsService

passport_router = Router(name="passport")

PASSPORT_SIZES = {
    "uz": ((413, 531), "#FFFFFF"),
    "ru": ((413, 531), "#FFFFFF"),
    "eu": ((413, 531), "#FFFFFF"),
    "us": ((600, 600), "#FFFFFF"),
}


async def _download(bot: Bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    bio = io.BytesIO()
    await bot.download_file(file.file_path, bio)
    return bio.getvalue()


@passport_router.callback_query(F.data == "tool:passport")
async def ask_passport(call: CallbackQuery, state: FSMContext):
    await state.set_state(PassportFlow.choose_size)
    await call.message.edit_text(
        "\ud83d\udcc4 <b>Pasport fotosurati</b>\n\nStandartni tanlang:",
        reply_markup=get_passport_kb(),
    )
    await call.answer()


@passport_router.callback_query(F.data.regexp(r"^pp:(uz|ru|eu|us)$"), PassportFlow.choose_size)
async def passport_chosen(call: CallbackQuery, state: FSMContext):
    code = call.data.split(":")[1]
    size, bg = PASSPORT_SIZES[code]
    await state.update_data(tool="passport", size=size, bg=bg)
    await state.set_state(PassportFlow.choose_color)
    await call.message.edit_text(
        f"\u2705 Tanlandi: <b>{code.upper()}</b> ({size[0]}x{size[1]})\n\nEndi rasm yuboring.",
        reply_markup=get_passport_kb(),
    )
    await call.answer()


@passport_router.message(PassportFlow.choose_color, F.photo)
async def process_passport(message: Message, state: FSMContext, bot: Bot, db_user, session):
    data = await state.get_data()
    size = data.get("size", (413, 531))
    bg = data.get("bg", "#FFFFFF")
    photo = message.photo[-1]
    img = await _download(bot, photo.file_id)
    ok, info = await check_and_increment_usage(session, db_user.id)
    if not ok:
        await message.answer(f"\ud83d\udeab Limit tugadi.")
        await state.clear()
        return
    status = await message.answer("\u23f3 Pasport fotosurati tayyorlanmoqda...")
    try:
        result = await effects_service.passport_photo(img, size=tuple(size), background_color=bg)
        out = BufferedInputFile(result, filename=f"passport_{size[0]}x{size[1]}.jpg")
        await message.answer_document(out, caption=f"\u2705 Pasport ({size[0]}x{size[1]}) tayyor!")
    except Exception as e:
        await status.edit_text(f"\u274c {e}")
    await status.delete()
    svc = AnalyticsService(session)
    await svc.track("tool_used", db_user.id, {"tool": "passport"})
    await state.clear()


__all__ = ["passport_router"]