from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Orqa fonni o'chirish", callback_data="info")],
        [InlineKeyboardButton(text="Referral", callback_data="referral"), InlineKeyboardButton(text="Premium", callback_data="premium")],
        [InlineKeyboardButton(text="Til", callback_data="language"), InlineKeyboardButton(text="Statistika", callback_data="stats")]
    ])


def subscription_keyboard(channels):
    buttons = [[InlineKeyboardButton(text=f"Kanal: {ch}", url=f"https://t.me/{ch.replace('@','')}")] for ch in channels]
    buttons.append([InlineKeyboardButton(text="Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="UZ", callback_data="lang_uz"), InlineKeyboardButton(text="RU", callback_data="lang_ru"), InlineKeyboardButton(text="EN", callback_data="lang_en")]
    ])


def referral_keyboard(bot_username):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ulashish", url=f"https://t.me/share/url?url=https://t.me/{bot_username}?start=ref")],
        [InlineKeyboardButton(text="Top", callback_data="ref_top"), InlineKeyboardButton(text="Orqaga", callback_data="back_menu")]
    ])


def premium_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="30 kun", callback_data="buy_premium_30"), InlineKeyboardButton(text="90 kun", callback_data="buy_premium_90")],
        [InlineKeyboardButton(text="Orqaga", callback_data="back_menu")]
    ])


def back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Orqaga", callback_data="back_menu")]])