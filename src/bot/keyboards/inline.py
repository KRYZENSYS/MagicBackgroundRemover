"""Inline keyboards (callback-driven)."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\u2702\ufe0f Fon o'chirish", callback_data="menu:tools"),
        InlineKeyboardButton(text="\ud83d\udd0e Kattalashtirish", callback_data="tool:upscale"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83c\udfa8 Orqa fon", callback_data="menu:background"),
        InlineKeyboardButton(text="\u2728 Effektlar", callback_data="menu:effects"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83d\udcc4 Pasport", callback_data="tool:passport"),
        InlineKeyboardButton(text="\ud83d\udcf8 Mahsulot", callback_data="tool:product"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83d\udc4e Yuz", callback_data="tool:face_enhance"),
        InlineKeyboardButton(text="\ud83c\udfaf Sifat", callback_data="tool:enhance"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83d\udc8e Premium", callback_data="menu:premium"),
        InlineKeyboardButton(text="\ud83d\udc65 Referral", callback_data="menu:referral"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83d\udc64 Profil", callback_data="menu:profile"),
        InlineKeyboardButton(text="\u2699\ufe0f Sozlamalar", callback_data="menu:settings"),
    )
    return b.as_markup()


def get_image_tools_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\u2702\ufe0f Fon o'chirish", callback_data="tool:bg_remove"),
        InlineKeyboardButton(text="\ud83d\udd0e Upscale 2x", callback_data="tool:upscale"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83d\udcdd Resize", callback_data="tool:resize"),
        InlineKeyboardButton(text="\ud83d\udcbe Compress", callback_data="tool:compress"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83c\udf10 Convert", callback_data="tool:convert"),
        InlineKeyboardButton(text="\ud83d\udd04 Rotate", callback_data="tool:rotate"),
    )
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Orqaga", callback_data="menu:main"))
    return b.as_markup()


def get_background_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\u2b55 Oq fon", callback_data="bg:white"),
        InlineKeyboardButton(text="\u26ab Qora fon", callback_data="bg:black"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83c\udfa8 Gradient", callback_data="bg:gradient"),
        InlineKeyboardButton(text="\ud83d\uddbc Maxsus rang", callback_data="bg:custom"),
    )
    b.row(InlineKeyboardButton(text="\ud83d\uddbc Boshqa rasm", callback_data="bg:image"))
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Orqaga", callback_data="menu:main"))
    return b.as_markup()


def get_effects_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\ud83d\udca7 Soya", callback_data="fx:shadow"),
        InlineKeyboardButton(text="\ud83d\udd0a Suv belgisi", callback_data="fx:watermark"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83c\udfa8 Sifat oshirish", callback_data="fx:enhance"),
        InlineKeyboardButton(text="\ud83c\udfaf Silliqlash", callback_data="fx:denoise"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83d\udd2e Aniqlik", callback_data="fx:sharpen"),
        InlineKeyboardButton(text="\ud83d\udd06 Yorqinlik", callback_data="fx:brighten"),
    )
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Orqaga", callback_data="menu:main"))
    return b.as_markup()


def get_upscale_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="2x (1024)", callback_data="up:2"),
        InlineKeyboardButton(text="4x (2048)", callback_data="up:4"),
    )
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Orqaga", callback_data="menu:main"))
    return b.as_markup()


def get_passport_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\ud83c\uddfa\ud83c\uddff Uzbek (35x45)", callback_data="pp:uz"),
        InlineKeyboardButton(text="\ud83c\uddf7\ud83c\uddfa Rossiya (35x45)", callback_data="pp:ru"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83c\uddeb\ud83c\uddf7 Yevropa (35x45)", callback_data="pp:eu"),
        InlineKeyboardButton(text="\ud83c\uddfa\ud83c\uddf8 AQSh (51x51)", callback_data="pp:us"),
    )
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Orqaga", callback_data="menu:main"))
    return b.as_markup()


def get_settings_kb(lang: str = "uz", user=None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\ud83c\udf10 Til", callback_data="menu:language"),
        InlineKeyboardButton(text="\ud83d\udd14 Bildirishnoma", callback_data="set:notif"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83c\udfa8 Sifat", callback_data="set:quality"),
        InlineKeyboardButton(text="\ud83d\udcca Limit", callback_data="set:limit"),
    )
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Orqaga", callback_data="menu:main"))
    return b.as_markup()


def get_premium_plans_kb(plans: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in plans:
        b.row(InlineKeyboardButton(
            text=f"\u2728 {p['name']} \u2014 {int(p['price']):,} {p['currency']}",
            callback_data=f"plan:{p['code']}",
        ))
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Orqaga", callback_data="menu:main"))
    return b.as_markup()


def get_payment_providers_kb(plan_code: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="\u2b50 Telegram Stars", callback_data=f"pay:stars:{plan_code}"))
    b.row(InlineKeyboardButton(text="\ud83d\udcb3 Click", callback_data=f"pay:click:{plan_code}"))
    b.row(InlineKeyboardButton(text="\ud83d\udc8e Payme", callback_data=f"pay:payme:{plan_code}"))
    b.row(InlineKeyboardButton(text="\ud83c\udf10 Stripe (karta)", callback_data=f"pay:stripe:{plan_code}"))
    b.row(InlineKeyboardButton(text="\u20bf Crypto", callback_data=f"pay:crypto:{plan_code}"))
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Orqaga", callback_data="menu:premium"))
    return b.as_markup()


def get_language_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\ud83c\uddfa\ud83c\uddfff O'zbek", callback_data="lang:uz"),
        InlineKeyboardButton(text="\ud83c\uddf7\ud83c\uddfa Русский", callback_data="lang:ru"),
    )
    b.row(InlineKeyboardButton(text="\ud83c\uddec\ud83c\udde7 English", callback_data="lang:en"))
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Orqaga", callback_data="menu:settings"))
    return b.as_markup()


def get_help_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\ud83d\udc4b Boshlash", callback_data="menu:main"),
        InlineKeyboardButton(text="\ud83d\udc8e Premium", callback_data="menu:premium"),
    )
    b.row(InlineKeyboardButton(text="\ud83d\udcdd Qo'llanma", url="https://telegra.ph/help"))
    b.row(InlineKeyboardButton(text="\ud83d\udcac Support", callback_data="menu:support"))
    return b.as_markup()


def get_admin_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\ud83d\udcca Statistika", callback_data="adm:stats"),
        InlineKeyboardButton(text="\ud83d\udc65 Users", callback_data="adm:users"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83d\udcb0 Payments", callback_data="adm:payments"),
        InlineKeyboardButton(text="\ud83d\udce2 Broadcast", callback_data="adm:broadcast"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83c\udfaf Promo kod", callback_data="adm:promo"),
        InlineKeyboardButton(text="\ud83d\udcb3 Plans", callback_data="adm:plans"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83d\udcc8 Analytics", callback_data="adm:analytics"),
        InlineKeyboardButton(text="\ud83d\udd27 Maintenance", callback_data="adm:maintenance"),
    )
    b.row(InlineKeyboardButton(text="\u25c0\ufe0f Chiqish", callback_data="menu:main"))
    return b.as_markup()


def get_confirm_kb(action: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\u2705 Ha", callback_data=f"confirm:{action}"),
        InlineKeyboardButton(text="\u274c Yo'q", callback_data="confirm:cancel"),
    )
    return b.as_markup()


def get_cancel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="\u274c Bekor qilish", callback_data="menu:cancel"))
    return b.as_markup()


def get_after_process_kb(tool: str = "bg_remove") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="\ud83d\udd04 Yana", callback_data=f"tool:{tool}"),
        InlineKeyboardButton(text="\ud83d\udcc4 PDF", callback_data="proc:pdf"),
    )
    b.row(
        InlineKeyboardButton(text="\ud83d\udce4 Ulashish", callback_data="proc:share"),
        InlineKeyboardButton(text="\ud83d\udc8e Premium", callback_data="menu:premium"),
    )
    b.row(InlineKeyboardButton(text="\ud83c\udfe0 Menyu", callback_data="menu:main"))
    return b.as_markup()


__all__ = [n for n in dir() if not n.startswith("_")]