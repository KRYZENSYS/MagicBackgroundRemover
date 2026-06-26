"""AI tool routers: upscale, enhance, face, passport, watermark."""
from __future__ import annotations

import io
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.services.ai.effects import effects_service
from src.services.ai.enhancer import image_enhancer
from src.services.ai.face import face_enhancer
from src.services.ai.upscaler import upscaler
from src.services.ai.validator import image_validator
from src.services.analytics.analytics import AnalyticsService
from src.services.user.subscription import SubscriptionService

router = Router(name="ai_tools")


async def _process(message: Message, session, tool_name: str, processor, **kwargs):
    if not message.photo:
        await message.answer("📸 Iltimos rasm yuboring.")
        return
    sub_svc = SubscriptionService(session)
    sub = await sub_svc.get_user_subscription(message.from_user.id)
    if sub and not sub.can_process():
        await message.answer("🚫 Limit tugadi. Premium: /premium")
        return
    photo = message.photo[-1]
    file = await message.bot.download(photo.file_id)
    raw = file.read()
    try:
        info = image_validator.inspect(raw)
    except ValueError as e:
        await message.answer(f"❌ {e}")
        return
    t0 = time.time()
    try:
        result = await processor(raw, **kwargs)
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
        return
    duration_ms = int((time.time() - t0) * 1000)
    analytics = AnalyticsService(session)
    await analytics.track(
        "tool_used",
        user_id=message.from_user.id,
        properties={"tool": tool_name, "ms": duration_ms},
    )
    if sub:
        await sub.record_usage()
    await message.answer_document(
        BufferedInputFile(result, filename=f"{tool_name}.png"),
        caption=f"✅ {tool_name} tayyor ({duration_ms} ms)",
    )


@router.message(Command("upscale"))
@router.message(F.text == "🔍 Kattalashtirish")
async def cmd_upscale(message: Message, session):
    # We don't know factor yet; expect next photo
    await message.answer("📸 Rasm yuboring — 2x kattalashtiraman.")


@router.callback_query(F.data == "tool:upscale2")
async def upscale2(call: CallbackQuery):
    await call.message.answer("📸 2x kattalashtirish uchun rasm yuboring.")
    await call.answer()


@router.callback_query(F.data == "tool:upscale4")
async def upscale4(call: CallbackQuery):
    await call.message.answer("📸 4x kattalashtirish uchun rasm yuboring.")
    await call.answer()


@router.callback_query(F.data == "tool:enhance")
async def enhance(call: CallbackQuery):
    await call.message.answer("✨ Sifatni oshirish uchun rasm yuboring.")
    await call.answer()


@router.callback_query(F.data == "tool:face")
async def face(call: CallbackQuery):
    await call.message.answer("👤 Yuzni kuchaytirish uchun rasm yuboring.")
    await call.answer()


@router.callback_query(F.data == "tool:passport")
async def passport(call: CallbackQuery):
    await call.message.answer("📄 Pasport fotosurati uchun rasm yuboring.")
    await call.answer()


@router.callback_query(F.data == "tool:shadow")
async def shadow(call: CallbackQuery):
    await call.message.answer("🌑 Soyali effekt uchun rasm yuboring.")
    await call.answer()


# Actual processors (triggered by callback after photo upload)
@router.message(F.photo, Command("upscale2"))
async def do_upscale2(message: Message, session):
    await _process(message, session, "upscale2x", upscaler.upscale, factor=2)


@router.message(F.photo, Command("upscale4"))
async def do_upscale4(message: Message, session):
    await _process(message, session, "upscale4x", upscaler.upscale, factor=4)


@router.message(F.photo, Command("enhance"))
async def do_enhance(message: Message, session):
    await _process(message, session, "enhance", image_enhancer.enhance)


@router.message(F.photo, Command("face"))
async def do_face(message: Message, session):
    await _process(message, session, "face_enhance", face_enhancer.enhance_face)


@router.message(F.photo, Command("passport"))
async def do_passport(message: Message, session):
    await _process(message, session, "passport", effects_service.passport_photo)


@router.message(F.photo, Command("shadow"))
async def do_shadow(message: Message, session):
    await _process(message, session, "shadow", effects_service.drop_shadow)


__all__ = ["router"]