from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_reply_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Rasm yuborish"), KeyboardButton(text="Statistika")],
        [KeyboardButton(text="Referral"), KeyboardButton(text="Premium")]
    ], resize_keyboard=True)