"""Upscale router (2x / 4x)."""
from __future__ import annotations

import io

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.keyboards.inline import get_upscale_kb
from src.bot.states import UpscaleFlow
from src.bot.utils.usage import check_and_increment_usage
from src.services.ai.upscaler import upscaler
from src.services.analytics.analytics import AnalyticsService

upscale_router = Router(name="upscale")


async def _download(bot: Bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    bio = io.BytesIO()
    await bot.download_file(file.file_path, bio)
    return bio.getvalue()


@upscale_router.callback_query(F.data == "tool:upscale")
async def ask_upscale(call: CallbackQuery, state: FSMContext):
    await state.set_state(UpscaleFlow.choose_factor)
    await call.message.edit_text(
        "\ud83d\udd0e <b>Kattalashtirish</b>\n\nQaysi darajani xohlaysiz?",
        reply_markup=get_upscale_kb(),
    )
    await call.answer()


@upscale_router.callback_query(F.data.regexp(r"^up:[24]$"), UpscaleFlow.choose_factor)
async def upscale_chosen(call: CallbackQuery, state: FSMContext):
    factor = int(call.data.split(":")[1])
    await state.update_data(tool="upscale", factor=factor)
    await state.set_state(UpscaleFlow.choose_factor)
    await call.message.edit_text(
        f"\u2705 {factor}x tanlandi. Endi rasm yuboring.",
        reply_markup=get_upscale_kb(),
    )
    await call.answer()


@upscale_router.message(UpscaleFlow.choose_factor, F.photo)
async def process_upscale(message: Message, state: FSMContext, bot: Bot, db_user, session):
    data = await state.get_data()
    factor = data.get("factor", 2)
    photo = message.photo[-1]
    img = await _download(bot, photo.file_id)
    ok, info = await check_and_increment_usage(session, db_user.id)
    if not ok:
        await message.answer(f"\ud83d\udeab Limit tugadi.")
        await state.clear()
        return
    status = await message.answer(f"\u23f3 Upscale {factor}x...")
    try:
        result = await upscaler.upscale(img, factor)
        out = BufferedInputFile(result, filename=f"upscale_{factor}x.png")
        await message.answer_document(out, caption=f"\u2705 {factor}x tayyor!")
    except Exception as e:
        await status.edit_text(f"\u274c {e}")
    await status.delete()
    svc = AnalyticsService(session)
    await svc.track("tool_used", db_user.id, {"tool": f"upscale_{factor}x"})
    await state.clear()


__all__ = ["upscale_router"]