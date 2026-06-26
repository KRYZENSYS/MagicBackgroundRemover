"""Image processing router (photo -> bg remove, upscale, etc.)."""
from __future__ import annotations

import io
import time

from aiogram import BaseMiddleware, F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.keyboards.inline import get_tools_kb, get_bg_kb
from src.bot.middlewares.throttling import ThrottlingMiddleware
from src.services.ai.bg_remover import bg_remover
from src.services.ai.enhancer import image_enhancer
from src.services.ai.effects import effects_service
from src.services.ai.face import face_enhancer
from src.services.ai.upscaler import upscaler
from src.services.ai.validator import image_validator
from src.services.analytics.analytics import AnalyticsService
from src.services.user.subscription import SubscriptionService

router = Router(name="image")
router.message.middleware(ThrottlingMiddleware(rate=2.0))


@router.message(F.photo)
async def on_photo(message: Message, session):
    user_id = message.from_user.id
    sub_svc = SubscriptionService(session)
    sub = await sub_svc.get_user_subscription(user_id)
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

    await message.answer("⏳ Qayta ishlanmoqda...")

    t0 = time.time()
    try:
        result = await bg_remover.remove_background(raw)
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
        return

    duration_ms = int((time.time() - t0) * 1000)

    # Track
    analytics = AnalyticsService(session)
    await analytics.track(
        "tool_used",
        user_id=user_id,
        properties={"tool": "bg_remove", "ms": duration_ms, "size": info["width"] * info["height"]},
    )
    if sub:
        await sub.record_usage()

    out = BufferedInputFile(result, filename="magicbg.png")
    await message.answer_document(
        out,
        caption=(
            f"✅ Tayyor! ({duration_ms} ms)\n\n"
            f"📐 {info['width']}x{info['height']}\n\n"
            "Qo'shimcha variantlar:"
        ),
        reply_markup=get_tools_kb(),
    )


@router.callback_query(F.data.startswith("tool:"))
async def on_tool(call: CallbackQuery, session):
    tool = call.data.split(":", 1)[1]
    await call.answer("⏳")
    # We don't have the original photo here; user needs to resend.
    # For demo: we just describe.
    desc = {
        "upscale": "🔍 Kattalashtirish 2x/4x",
        "enhance": "✨ Sifatni oshirish",
        "face": "👤 Yuzni kuchaytirish",
        "shadow": "🌑 Soyali effekt",
        "passport": "📄 Pasport fotosurati",
        "watermark": "🔖 Suv belgisi",
        "crop": "✂️ Kesish",
        "convert": "🔄 Format konvertatsiya",
    }.get(tool, tool)
    await call.message.answer(f"📨 Yangi rasm yuboring — men «{desc}» qilaman.")


@router.callback_query(F.data.startswith("bg:"))
async def on_bg(call: CallbackQuery, session):
    kind = call.data.split(":", 1)[1]
    await call.answer("📨 Yangi rasm yuboring — men fonni o'zgartiraman.")
    await call.message.answer("🎨 Orqa fon uchun rasm yuboring.")


__all__ = ["router"]