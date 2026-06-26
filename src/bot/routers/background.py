"""Background change flows: white, black, gradient, custom color, image background."""
from __future__ import annotations

import io
import re

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.keyboards.inline import get_cancel_kb
from src.bot.states import BackgroundFlow
from src.bot.utils.usage import check_and_increment_usage
from src.services.ai.bg_remover import bg_remover
from src.services.analytics.analytics import AnalyticsService

background_router = Router(name="background")

HEX_RE = re.compile(r"^#?([A-Fa-f0-9]{6})$")


async def _download(bot: Bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    bio = io.BytesIO()
    await bot.download_file(file.file_path, bio)
    return bio.getvalue()


@background_router.callback_query(F.data.startswith("bg:"))
async def choose_bg(call: CallbackQuery, state: FSMContext):
    action = call.data.split(":")[1]
    if action in ("white", "black"):
        color = "#FFFFFF" if action == "white" else "#000000"
        await state.update_data(tool="bg_color", color=color)
        await state.set_state(BackgroundFlow.choose_color)
        await call.message.edit_text(
            f"\ud83c\udfa8 <b>{'Oq' if action == 'white' else 'Qora'} fon</b> tanlandi.\n\n"
            f"Endi rasm yuboring.",
            reply_markup=get_cancel_kb(),
        )
    elif action == "custom":
        await state.set_state(BackgroundFlow.choose_color)
        await call.message.edit_text(
            "\ud83d\uddbc <b>Maxsus rang</b>\n\n"
            "RGB kod yuboring (masalan: <code>#FF5733</code> yoki <code>FF5733</code>):",
            reply_markup=get_cancel_kb(),
        )
    elif action == "gradient":
        await state.set_state(BackgroundFlow.enter_gradient)
        await call.message.edit_text(
            "\ud83c\udfa8 <b>Gradient</b>\n\n"
            "Ikki rang yuboring:\n<code>#FF5733,#3498DB</code>",
            reply_markup=get_cancel_kb(),
        )
    elif action == "image":
        await state.set_state(BackgroundFlow.enter_image)
        await call.message.edit_text(
            "\ud83d\uddbc <b>Orqa fon rasmi</b>\n\n"
            "Orqa fon sifatida ishlatmoqchi bo'lgan rasmni yuboring.",
            reply_markup=get_cancel_kb(),
        )
    await call.answer()


@background_router.message(BackgroundFlow.choose_color, F.text)
async def custom_color(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if HEX_RE.match(text):
        color = "#" + HEX_RE.match(text).group(1).upper()
        await state.update_data(tool="bg_color", color=color)
        await message.answer(
            f"\u2705 Rang qabul qilindi: <code>{color}</code>\n\nEndi rasm yuboring.",
            reply_markup=get_cancel_kb(),
        )
    else:
        await message.answer("\u274c Noto'g'ri format. Masalan: <code>#FF5733</code>")


@background_router.message(BackgroundFlow.enter_gradient, F.text)
async def gradient_input(message: Message, state: FSMContext):
    parts = (message.text or "").replace(" ", "").split(",")
    if len(parts) != 2 or not all(HEX_RE.match(p) for p in parts):
        await message.answer("\u274c Format: <code>#FF5733,#3498DB</code>")
        return
    a, b = ("#" + HEX_RE.match(parts[0]).group(1).upper(), "#" + HEX_RE.match(parts[1]).group(1).upper())
    await state.update_data(tool="bg_gradient", color_a=a, color_b=b)
    await message.answer(
        f"\u2705 Gradient: {a} \u2192 {b}\n\nEndi rasm yuboring.",
        reply_markup=get_cancel_kb(),
    )


@background_router.message(BackgroundFlow.enter_image, F.photo)
async def bg_image_received(message: Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    bg_bytes = await _download(bot, photo.file_id)
    await state.update_data(tool="bg_image", bg_bytes_id=photo.file_id, bg_size=len(bg_bytes))
    await state.set_state(BackgroundFlow.choose_color)
    await message.answer("\u2705 Orqa fon rasmi qabul qilindi. Endi asosiy rasmni yuboring.", reply_markup=get_cancel_kb())


@background_router.message(BackgroundFlow.choose_color, F.photo)
async def process_color_bg(message: Message, state: FSMContext, bot: Bot, db_user, session):
    data = await state.get_data()
    photo = message.photo[-1]
    img = await _download(bot, photo.file_id)
    ok, info = await check_and_increment_usage(session, db_user.id)
    if not ok:
        await message.answer(f"\ud83d\udeab Limit tugadi ({info.get('limit', 5)}). Premium: /premium")
        await state.clear()
        return
    status = await message.answer("\u23f3 Ishlanmoqda...")
    try:
        result = await bg_remover.solid_color_background(img, data.get("color", "#FFFFFF"))
        out = BufferedInputFile(result, filename="bg_color.png")
        await message.answer_document(out, caption=f"\u2705 Fon: {data.get('color')}")
    except Exception as e:
        await status.edit_text(f"\u274c {e}")
        return
    await status.delete()
    AnalyticsService(session).track_sync if hasattr(AnalyticsService(session), "track_sync") else None
    svc = AnalyticsService(session)
    await svc.track("tool_used", db_user.id, {"tool": "bg_color"})
    await state.clear()


@background_router.message(BackgroundFlow.choose_color, F.photo)
async def process_gradient_bg(message: Message, state: FSMContext, bot: Bot, db_user, session):
    data = await state.get_data()
    if data.get("tool") != "bg_gradient":
        return
    photo = message.photo[-1]
    img = await _download(bot, photo.file_id)
    ok, info = await check_and_increment_usage(session, db_user.id)
    if not ok:
        await message.answer(f"\ud83d\udeab Limit tugadi.")
        await state.clear()
        return
    status = await message.answer("\u23f3 Ishlanmoqda...")
    try:
        result = await bg_remover.gradient_background(
            img,
            data["color_a"],
            data["color_b"],
            data.get("direction", "vertical"),
        )
        out = BufferedInputFile(result, filename="bg_gradient.png")
        await message.answer_document(out, caption=f"\u2705 Gradient: {data['color_a']} \u2192 {data['color_b']}")
    except Exception as e:
        await status.edit_text(f"\u274c {e}")
    await status.delete()
    svc = AnalyticsService(session)
    await svc.track("tool_used", db_user.id, {"tool": "bg_gradient"})
    await state.clear()


@background_router.message(BackgroundFlow.choose_color, F.photo)
async def process_image_bg(message: Message, state: FSMContext, bot: Bot, db_user, session):
    data = await state.get_data()
    if data.get("tool") != "bg_image":
        return
    main_photo = message.photo[-1]
    img = await _download(bot, main_photo.file_id)
    bg_bytes = await _download(bot, data["bg_bytes_id"])
    ok, info = await check_and_increment_usage(session, db_user.id)
    if not ok:
        await message.answer(f"\ud83d\udeab Limit tugadi.")
        await state.clear()
        return
    status = await message.answer("\u23f3 Ishlanmoqda...")
    try:
        result = await bg_remover.image_background(img, bg_bytes)
        out = BufferedInputFile(result, filename="bg_image.png")
        await message.answer_document(out, caption="\u2705 Tayyor!")
    except Exception as e:
        await status.edit_text(f"\u274c {e}")
    await status.delete()
    svc = AnalyticsService(session)
    await svc.track("tool_used", db_user.id, {"tool": "bg_image"})
    await state.clear()


__all__ = ["background_router"]