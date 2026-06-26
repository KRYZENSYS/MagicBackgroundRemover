"""Generic photo handler that detects what tool to use."""
from __future__ import annotations

import asyncio
import io
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from src.bot.states import ImageProcessing
from src.bot.utils.usage import check_and_increment_usage
from src.config.logging import logger
from src.services.ai.bg_remover import bg_remover
from src.services.ai.enhancer import image_enhancer
from src.services.ai.validator import image_validator
from src.services.image.processor import image_processor
from src.services.image.converter import image_converter
from src.services.analytics.analytics import AnalyticsService
from src.services.notification.templates import NotificationTemplates

image_router = Router(name="image")


async def _download(bot: Bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    bio = io.BytesIO()
    await bot.download_file(file.file_path, bio)
    return bio.getvalue()


@image_router.message(F.photo, ImageProcessing.waiting_photo)
async def process_pending_photo(message: Message, state: FSMContext, bot: Bot, db_user, session):
    """User uploaded a photo while a tool is awaiting input."""
    data = await state.get_data()
    tool = data.get("tool")
    options = data.get("options", {})

    photo = message.photo[-1]
    img_bytes = await _download(bot, photo.file_id)

    ok, info = await check_and_increment_usage(session, db_user.id)
    if not ok:
        await message.answer(NotificationTemplates.daily_limit_reached(info.get("limit", 5), db_user.language or "uz"))
        await state.clear()
        return

    try:
        meta = image_validator.inspect(img_bytes)
    except Exception as e:
        await message.answer(f"❌ Rasm xato: {e}")
        await state.clear()
        return

    status = await message.answer("⏳ <b>Ishlanmoqda...</b>")
    result_bytes = await _dispatch(tool, img_bytes, options)
    analytics = AnalyticsService(session)
    await analytics.track("tool_used", db_user.id, {"tool": tool})
    await analytics.increment(f"tool:{tool}")

    out = BufferedInputFile(result_bytes, filename=f"{tool}_{photo.file_unique_id}.png")
    await message.answer_photo(out, caption=f"✅ Tayyor! ({tool})")
    await status.delete()
    await state.clear()


@image_router.message(F.photo)
async def default_remove_background(message: Message, bot: Bot, db_user, session):
    """No tool selected - apply default background removal."""
    photo = message.photo[-1]
    img_bytes = await _download(bot, photo.file_id)

    ok, info = await check_and_increment_usage(session, db_user.id)
    if not ok:
        await message.answer(NotificationTemplates.daily_limit_reached(info.get("limit", 5), db_user.language or "uz"))
        return

    try:
        image_validator.inspect(img_bytes)
    except Exception as e:
        await message.answer(f"❌ {e}")
        return

    status = await message.answer("⏳ <b>Fon o'chirilmoqda...</b>")
    try:
        result = await bg_remover.remove_background(img_bytes)
    except Exception as e:
        await status.edit_text(f"❌ Xato: {e}")
        return

    analytics = AnalyticsService(session)
    await analytics.track("tool_used", db_user.id, {"tool": "bg_removal"})
    await analytics.increment("tool:bg_removal")

    out = BufferedInputFile(result, filename=f"nobg_{photo.file_unique_id}.png")
    await message.answer_document(out, caption="✅ Fon o'chirildi!\n📌 PNG formatda saqlab oling.")
    await status.delete()


@image_router.message(F.document)
async def handle_document(message: Message, bot: Bot, db_user, session):
    doc = message.document
    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        return
    img_bytes = await _download(bot, doc.file_id)
    ok, info = await check_and_increment_usage(session, db_user.id)
    if not ok:
        await message.answer(NotificationTemplates.daily_limit_reached(info.get("limit", 5), db_user.language or "uz"))
        return
    status = await message.answer("⏳ <b>Ishlanmoqda...</b>")
    try:
        result = await bg_remover.remove_background(img_bytes)
    except Exception as e:
        await status.edit_text(f"❌ {e}")
        return
    out = BufferedInputFile(result, filename=f"nobg_{doc.file_name or 'image'}.png")
    await message.answer_document(out, caption="✅ Tayyor!")
    await status.delete()


async def _dispatch(tool: str, img_bytes: bytes, options: dict) -> bytes:
    """Run the appropriate tool with given options."""
    if tool == "bg_remove":
        return await bg_remover.remove_background(img_bytes)
    if tool == "bg_color":
        return await bg_remover.solid_color_background(img_bytes, options.get("color", "#FFFFFF"))
    if tool == "bg_gradient":
        return await bg_remover.gradient_background(
            img_bytes,
            options.get("color_a", "#FFFFFF"),
            options.get("color_b", "#000000"),
            options.get("direction", "vertical"),
        )
    if tool == "upscale":
        factor = int(options.get("factor", 2))
        from src.services.ai.upscaler import upscaler
        return await upscaler.upscale(img_bytes, factor)
    if tool == "passport":
        from src.services.ai.effects import effects_service
        return await effects_service.passport_photo(
            img_bytes,
            size=tuple(options.get("size", (413, 531))),
            background_color=options.get("bg", "#FFFFFF"),
        )
    if tool == "product":
        from src.services.ai.effects import effects_service
        return await effects_service.product_photo(img_bytes)
    if tool == "face_enhance":
        from src.services.ai.face import face_enhancer
        return await face_enhancer.enhance_face(img_bytes)
    if tool == "denoise":
        return await image_enhancer.denoise(img_bytes)
    if tool == "sharpen":
        return await image_enhancer.sharpen(img_bytes)
    if tool == "enhance":
        return await image_enhancer.enhance(img_bytes)
    if tool == "resize":
        return await image_processor.resize(
            img_bytes,
            width=options.get("width"),
            height=options.get("height"),
            keep_aspect=options.get("keep_aspect", True),
        )
    if tool == "compress":
        return await image_processor.compress(img_bytes, options.get("quality", 70))
    if tool == "convert":
        return await image_converter.convert(img_bytes, options.get("format", "PNG"))
    if tool == "rotate":
        return await image_processor.rotate(img_bytes, options.get("degrees", 90))
    if tool == "flip":
        return await image_processor.flip(img_bytes, options.get("direction", "horizontal"))
    raise ValueError(f"Unknown tool: {tool}")


__all__ = ["image_router"]