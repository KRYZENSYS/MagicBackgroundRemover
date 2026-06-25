from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import models as db
from keyboards.inline import premium_keyboard, main_menu_keyboard

router = Router()


@router.callback_query(F.data == "premium")
async def prem_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if user and user["premium"]:
        text = "Premium faol! Cheksiz foydalaning."
    else:
        text = "Premium:\n\nCheksiz rasm\nTezkor ishlov\nBonuslar\n\nTanlang:"
    await callback.message.edit_text(text, reply_markup=premium_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("buy_premium_"))
async def buy(callback: CallbackQuery):
    days = int(callback.data.split("_")[-1])
    await db.set_premium(callback.from_user.id, days)
    await callback.message.edit_text(f"Premium {days} kun berildi!", reply_markup=main_menu_keyboard())
    await callback.answer()