"""Settings: language, notifications, quality, limit info."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import get_language_kb
from src.bot.utils.usage import get_remaining_quota

settings_router = Router(name="settings")


@settings_router.message(Command("settings"))
async def cmd_settings(message: Message, db_user):
    text = (
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"🌐 Til: {(db_user.language or 'uz').upper()}\n"
        f"🔔 Bildirishnomalar: {'✅' if db_user.notifications_enabled else '❌'}\n"
        f"🎨 Sifat: {db_user.quality_preference or 'auto'}\n"
    )
    await message.answer(text, reply_markup=get_language_kb())


@settings_router.callback_query(F.data == "set:notif")
async def toggle_notif(call: CallbackQuery, db_user, session):
    db_user.notifications_enabled = not db_user.notifications_enabled
    await session.commit()
    state = "✅ yoqildi" if db_user.notifications_enabled else "❌ o'chirildi"
    await call.message.edit_text(f"🔔 Bildirishnomalar {state}")
    await call.answer()


@settings_router.callback_query(F.data == "set:quality")
async def quality_picker(call: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ Tez", callback_data="q:fast"),
            InlineKeyboardButton(text="🎯 Balanslangan", callback_data="q:balanced"),
        ],
        [InlineKeyboardButton(text="💎 Sifat", callback_data="q:quality")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="menu:settings")],
    ])
    await call.message.edit_text("🎨 Sifatni tanlang:", reply_markup=kb)
    await call.answer()


@settings_router.callback_query(F.data.startswith("q:"))
async def set_quality(call: CallbackQuery, db_user, session):
    level = call.data.split(":")[1]
    db_user.quality_preference = level
    await session.commit()
    await call.message.edit_text(f"✅ Sifat: {level}")
    await call.answer()


@settings_router.callback_query(F.data == "set:limit")
async def show_limit(call: CallbackQuery, session, db_user):
    info = await get_remaining_quota(session, db_user.id)
    text = (
        f"📊 <b>Sizning limitingiz</b>\n\n"
        f"🔄 Bugun qolgan: <b>{info['remaining']}/{info['limit']}</b>\n"
        f"💎 Premium: {'✅' if info['is_premium'] else '❌'}\n"
        f"📈 Jami ishlangan: <b>{info.get('total', 0)}</b>"
    )
    await call.message.edit_text(text, reply_markup=get_language_kb())
    await call.answer()


__all__ = ["settings_router"]