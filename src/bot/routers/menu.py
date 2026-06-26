"""Main menu callback routing."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import (
    get_main_menu_kb,
    get_background_kb,
    get_effects_kb,
    get_settings_kb,
    get_image_tools_kb,
)
from src.bot.keyboards.reply import get_main_reply_kb

menu_router = Router(name="menu")


@menu_router.callback_query(F.data == "menu:main")
async def back_to_main(call: CallbackQuery, db_user):
    await call.message.edit_text(
        "🏠 <b>Asosiy menyu</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=get_main_menu_kb(db_user.language or "uz"),
    )
    await call.answer()


@menu_router.callback_query(F.data == "menu:tools")
async def show_tools(call: CallbackQuery, db_user):
    await call.message.edit_text(
        "🛠 <b>Vositalar</b>\n\nRasmlaringiz bilan nima qilmoqchisiz?",
        reply_markup=get_image_tools_kb(db_user.language or "uz"),
    )
    await call.answer()


@menu_router.callback_query(F.data == "menu:background")
async def show_background(call: CallbackQuery, db_user):
    await call.message.edit_text(
        "🎨 <b>Orqa fon bilan ishlash</b>\n\nVariantni tanlang:",
        reply_markup=get_background_kb(),
    )
    await call.answer()


@menu_router.callback_query(F.data == "menu:effects")
async def show_effects(call: CallbackQuery, db_user):
    await call.message.edit_text(
        "✨ <b>Effektlar</b>\n\nVariantni tanlang:",
        reply_markup=get_effects_kb(),
    )
    await call.answer()


@menu_router.callback_query(F.data == "menu:settings")
async def show_settings(call: CallbackQuery, db_user):
    await call.message.edit_text(
        "⚙️ <b>Sozlamalar</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=get_settings_kb(db_user.language or "uz", db_user),
    )
    await call.answer()


@menu_router.callback_query(F.data == "menu:profile")
async def show_profile(call: CallbackQuery, db_user):
    is_premium = db_user.is_premium and db_user.premium_until
    premium_until = db_user.premium_until.strftime("%d.%m.%Y") if db_user.premium_until else "\u2014"
    text = (
        f"👤 <b>Profil</b>\n\n"
        f"🆔 ID: <code>{db_user.id}</code>\n"
        f"👤 Ism: {db_user.first_name or '\u2014'} {db_user.last_name or ''}\n"
        f"📛 Username: @{db_user.username or '\u2014'}\n"
        f"🌐 Til: {(db_user.language or 'uz').upper()}\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"   Jami ishlangan: <b>{db_user.total_processed}</b>\n"
        f"   Bugun: <b>{db_user.daily_processed}</b>\n"
        f"   Referrallar: <b>{db_user.referral_count}</b>\n\n"
        f"💎 <b>Premium:</b> {'✅ Faol' if is_premium else '❌ Faol emas'}\n"
        f"   Tugash: <b>{premium_until}</b>"
    )
    await call.message.edit_text(text, reply_markup=get_main_menu_kb(db_user.language or "uz"))
    await call.answer()


@menu_router.message(F.text.in_({"🏠 Menyu", "📖 Yordam", "💎 Premium", "⚙️ Sozlamalar", "👥 Referral"}))
async def reply_menu(message: Message, db_user):
    text = message.text
    if text in ("🏠 Menyu",):
        await message.answer("🏠 Asosiy menyu:", reply_markup=get_main_menu_kb(db_user.language or "uz"))
    elif text in ("📖 Yordam",):
        await message.answer("📖 Yordam uchun /help buyrug'ini yuboring.")
    elif text in ("💎 Premium",):
        await message.answer("Premium bo'limi:", reply_markup=get_main_menu_kb(db_user.language or "uz"))
    elif text in ("⚙️ Sozlamalar",):
        await message.answer("⚙️ Sozlamalar:", reply_markup=get_settings_kb(db_user.language or "uz", db_user))
    elif text in ("👥 Referral",):
        bot_username = (await message.bot.me()).username
        link = f"https://t.me/{bot_username}?start=ref_{db_user.id}"
        await message.answer(
            f"👥 <b>Referral tizimi</b>\n\n"
            f"Do'stlarni taklif qiling va premium oling.\n"
            f"Sizning linkingiz:\n<code>{link}</code>\n\n"
            f"📊 Taklif qilganlar: <b>{db_user.referral_count}</b>",
            reply_markup=get_main_menu_kb(db_user.language or "uz"),
        )


__all__ = ["menu_router"]