"""Reply keyboards (persistent menu)."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_reply() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✂️ BG o'chirish")],
            [
                KeyboardButton(text="👤 Profil"),
                KeyboardButton(text="💎 Premium"),
            ],
            [
                KeyboardButton(text="👥 Referral"),
                KeyboardButton(text="📊 Statistika"),
            ],
            [
                KeyboardButton(text="⚙️ Sozlamalar"),
                KeyboardButton(text="🌐 Til"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Rasm yuboring...",
    )