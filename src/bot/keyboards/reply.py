"""Persistent reply keyboard."""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_reply_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(
        KeyboardButton(text="\u2702\ufe0f Fon o'chirish"),
        KeyboardButton(text="\ud83d\udd0e Kattalashtirish"),
    )
    b.row(
        KeyboardButton(text="\ud83d\udc64 Profil"),
        KeyboardButton(text="\ud83d\udc8e Premium"),
    )
    b.row(
        KeyboardButton(text="\ud83d\udc65 Referral"),
        KeyboardButton(text="\u2699\ufe0f Sozlamalar"),
    )
    b.row(KeyboardButton(text="\ud83d\udcac Support"))
    return b.as_markup(resize_keyboard=True, input_field_placeholder="Rasm yuboring...")


__all__ = ["get_main_reply_kb"]