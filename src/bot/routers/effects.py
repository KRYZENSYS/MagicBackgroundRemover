"""Effects router: shadow, watermark, enhance, denoise, sharpen, brighten, face enhance, product photo."""
from __future__ import annotations

import io

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.states import ImageProcessing
from src.bot.utils.usage import check_and_increment_usage
from src.services.ai.effects import effects_service
from src.services.ai.enhancer import image_enhancer
from src.services.ai.face import face_enhancer
from src.services.analytics.analytics import AnalyticsService

effects_router = Router(name="effects")

EFFECT_MAP = {
    "fx:shadow": ("shadow", "shadow"),
    "fx:watermark": ("watermark", "watermark"),
    "fx:enhance": ("enhance", "enhance"),
    "fx:denoise": ("denoise", "denoise"),
    "fx:sharpen": ("sharpen", "sharpen"),
    "fx:brighten": ("brighten", "brighten"),
}


async def _download(bot: Bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    bio = io.BytesIO()
    await bot.download_file(file.file_path, bio)
    return bio.getvalue()


@effects_router.callback_query(F.data.in_(EFFECT_MAP.keys()))
async def pick_effect(call: CallbackQuery, state: FSMContext):
    tool, _ = EFFECT_MAP[call.data]
    await state.set_state(ImageProcessing.waiting_photo)
    await state.update_data(tool=tool)
    await call.message.edit_text(
        f"✨ <b>{tool.capitalize()}</b> tanlandi.\n\nRasm yuboring.",
    )
    await call.answer()


@effects_router.callback_query(F.data == "tool:face_enhance")
async def pick_face(call: CallbackQuery, state: FSMContext):
    await state.set_state(ImageProcessing.waiting_photo)
    await state.update_data(tool="face_enhance")
    await call.message.edit_text("👎 <b>Yuz sifatini oshirish</b>\n\nAniq yuz bilan rasm yuboring.")
    await call.answer()


@effects_router.callback_query(F.data == "tool:product")
async def pick_product(call: CallbackQuery, state: FSMContext):
    await state.set_state(ImageProcessing.waiting_photo)
    await state.update_data(tool="product")
    await call.message.edit_text("📸 <b>Mahsulot fotosurati</b>\n\nMahsulot rasmini yuboring.")
    await call.answer()


@effects_router.message(ImageProcessing.waiting_photo, F.photo)
async def run_effect(message: Message, state: FSMContext, bot: Bot, db_user, session):
    data = await state.get_data()
    tool = data.get("tool")
    photo = message.photo[-1]
    img = await _download(bot, photo.file_id)
    ok, info = await check_and_increment_usage(session, db_user.id)
    if not ok:
        await message.answer(f"🚫 Limit tugadi.")
        await state.clear()
        return
    status = await message.answer("⏳ Ishlanmoqda...")
    try:
        result = await _run_effect(tool, img)
        out = BufferedInputFile(result, filename=f"{tool}.png")
        await message.answer_document(out, caption=f"✅ Tayyor: {tool}")
    except Exception as e:
        await status.edit_text(f"❌ {e}")
    await status.delete()
    svc = AnalyticsService(session)
    await svc.track("tool_used", db_user.id, {"tool": tool})
    await state.clear()


async def _run_effect(tool: str, img: bytes) -> bytes:
    if tool == "shadow":
        return await effects_service.drop_shadow(img)
    if tool == "watermark":
        return await effects_service.add_text_watermark(img, "MagicBG")
    if tool == "enhance":
        return await image_enhancer.enhance(img)
    if tool == "denoise":
        return await image_enhancer.denoise(img)
    if tool == "sharpen":
        return await image_enhancer.sharpen(img)
    if tool == "brighten":
        return await image_enhancer.brighten(img, factor=1.3)
    if tool == "face_enhance":
        return await face_enhancer.enhance_face(img)
    if tool == "product":
        return await effects_service.product_photo(img)
    raise ValueError(f"Unknown effect: {tool}")


__all__ = ["effects_router"]