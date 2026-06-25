from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from config import MESSAGES, DEFAULT_LANGUAGE, FREE_DAILY_LIMIT, REQUIRED_CHANNELS, DATABASE_PATH
from database import models as db
from keyboards.inline import main_menu_keyboard, subscription_keyboard, language_keyboard
from utils.checker import check_subscription
import aiosqlite

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split(); invited_by = None
    if len(args) > 1 and args[1].startswith("ref"):
        try: invited_by = int(args[1].replace("ref", ""))
        except: pass

    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name, invited_by)
        user = await db.get_user(message.from_user.id)
    await db.update_last_active(message.from_user.id)

    if user and user["banned"]:
        await message.answer("Bloklangansiz!"); return

    if not await check_subscription(message.bot, message.from_user.id):
        await message.answer("Kanalga obuna bo'ling:", reply_markup=subscription_keyboard(REQUIRED_CHANNELS)); return

    lang = user["language"] if user else DEFAULT_LANGUAGE
    await message.answer(MESSAGES[lang]["welcome"].format(name=message.from_user.first_name), reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(callback: CallbackQuery):
    if await check_subscription(callback.bot, callback.from_user.id):
        await callback.message.answer("Tayyor!", reply_markup=main_menu_keyboard())
        await callback.answer("OK")
    else:
        await callback.answer("Avval obuna bo'ling!", show_alert=True)


@router.callback_query(F.data == "language")
async def lang_cb(callback: CallbackQuery):
    await callback.message.edit_text("Tilni tanlang:", reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        await conn.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (lang, callback.from_user.id)); await conn.commit()
    await callback.message.edit_text(f"Til: {lang.upper()}", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "stats")
async def stats_cb(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    count = await db.get_referral_count(callback.from_user.id)
    total = user["total_processed"] if user else 0
    daily = user["daily_processed"] if user else 0
    prem = "Premium" if user and user["premium"] else "Free"
    await callback.message.edit_text(f"Statistika:\n\nRasmlar: {total}\nBugun: {daily}\nStatus: {prem}\nReferral: {count}", reply_markup=main_menu_keyboard())
    await callback.answer()