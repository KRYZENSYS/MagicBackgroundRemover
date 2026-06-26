"""Inline keyboards for the bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu(user=None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✂️ BG o'chirish", callback_data="tool_bg_remove"),
        InlineKeyboardButton(text="🎨 BG almashtirish", callback_data="tool_bg_replace"),
    )
    builder.row(
        InlineKeyboardButton(text="⬆️ Upscale", callback_data="tool_upscale"),
        InlineKeyboardButton(text="✨ Enhance", callback_data="tool_enhance"),
    )
    builder.row(
        InlineKeyboardButton(text="📄 Passport", callback_data="tool_passport"),
        InlineKeyboardButton(text="🌫️ Portrait", callback_data="tool_portrait"),
    )
    builder.row(
        InlineKeyboardButton(text="💎 Premium", callback_data="premium"),
        InlineKeyboardButton(text="👥 Referral", callback_data="referral"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Profil", callback_data="profile"),
        InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings"),
    )
    return builder.as_markup()


def language_select() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
    )
    return builder.as_markup()


def image_tools() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✂️ BG remove", callback_data="process_bg_remove"),
        InlineKeyboardButton(text="⬆️ Upscale 2x", callback_data="process_upscale_2x"),
    )
    builder.row(
        InlineKeyboardButton(text="🎨 White BG", callback_data="process_white_bg"),
        InlineKeyboardButton(text="⚫ Black BG", callback_data="process_black_bg"),
    )
    builder.row(
        InlineKeyboardButton(text="🌈 Gradient", callback_data="process_gradient"),
        InlineKeyboardButton(text="✨ Enhance", callback_data="process_enhance"),
    )
    builder.row(
        InlineKeyboardButton(text="📄 Passport", callback_data="process_passport"),
        InlineKeyboardButton(text="🌫️ Portrait", callback_data="process_portrait"),
    )
    builder.row(InlineKeyboardButton(text="« Menyu", callback_data="menu_main"))
    return builder.as_markup()


def premium_plans(plans) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.row(InlineKeyboardButton(
            text=f"{plan.name} — {plan.price} {plan.currency}",
            callback_data=f"plan_{plan.id}",
        ))
    builder.row(InlineKeyboardButton(text="« Orqaga", callback_data="menu_main"))
    return builder.as_markup()


def payment_methods(plan_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⭐ Telegram Stars", callback_data=f"pay_telegram_{plan_id}"))
    builder.row(InlineKeyboardButton(text="💳 Click", callback_data=f"pay_click_{plan_id}"))
    builder.row(InlineKeyboardButton(text="💎 Payme", callback_data=f"pay_payme_{plan_id}"))
    builder.row(InlineKeyboardButton(text="🌐 Stripe", callback_data=f"pay_stripe_{plan_id}"))
    builder.row(InlineKeyboardButton(text="₿ Crypto", callback_data=f"pay_crypto_{plan_id}"))
    builder.row(InlineKeyboardButton(text="« Orqaga", callback_data="premium"))
    return builder.as_markup()


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
        InlineKeyboardButton(text="👥 Users", callback_data="admin_users"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Payments", callback_data="admin_payments"),
        InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast"),
    )
    builder.row(
        InlineKeyboardButton(text="🎫 Promo", callback_data="admin_promo"),
        InlineKeyboardButton(text="🔧 Maintenance", callback_data="admin_maint"),
    )
    return builder.as_markup()


def settings_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌐 Til", callback_data="set_language"),
        InlineKeyboardButton(text="🎨 Tema", callback_data="set_theme"),
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Bildirishnomalar", callback_data="set_notifications"),
        InlineKeyboardButton(text="⭐ Sevimli tool", callback_data="set_favorites"),
    )
    builder.row(InlineKeyboardButton(text="« Menyu", callback_data="menu_main"))
    return builder.as_markup()


def after_process() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔁 Boshqa tool", callback_data="menu_main"),
        InlineKeyboardButton(text="📤 Ulashish", callback_data="share"),
    )
    return builder.as_markup()