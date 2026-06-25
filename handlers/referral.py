from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import MESSAGES, DEFAULT_LANGUAGE
from database import models as db
from keyboards.inline import referral_keyboard

router = Router()


@router.callback_query(F.data == "referral")
async def ref_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else DEFAULT_LANGUAGE
    count = await db.get_referral_count(callback.from_user.id)
    bot_username = (await callback.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref{callback.from_user.id}"
    text = MESSAGES[lang]["referral_invite"].format(link=link, count=count)
    await callback.message.edit_text(text, reply_markup=referral_keyboard(bot_username))
    await callback.answer()


@router.callback_query(F.data == "ref_top")
async def ref_top(callback: CallbackQuery):
    top = await db.get_referral_leaderboard(10)
    text = "Top referrers:\n\n"
    for i, u in enumerate(top, 1):
        name = u["first_name"] or u["username"] or "Anonim"
        text += f"{i}. {name} - {u['ref_count']}\n"
    await callback.message.answer(text)
    await callback.answer()