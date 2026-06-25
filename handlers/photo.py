from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.enums import ChatAction
from config import FREE_DAILY_LIMIT, PREMIUM_DAILY_LIMIT, MESSAGES
from database import models as db
from utils.bg_remove import remove_background
from utils.checker import check_subscription
from utils.logger import logger

router = Router()


@router.message(F.photo)
async def handle_photo(message: Message):
    uid = message.from_user.id
    if not await check_subscription(message.bot, uid):
        await message.answer("Avval kanalga obuna bo'ling!"); return
    user = await db.get_user(uid)
    if user and user["banned"]: return
    limit = PREMIUM_DAILY_LIMIT if user and user["premium"] else FREE_DAILY_LIMIT
    if not await db.check_daily_limit(uid, limit):
        await message.answer(f"Kunlik limit tugadi ({limit})!"); return

    status = await message.answer("Orqa fon o'chirilmoqda...")
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        fbytes = await message.bot.download_file(file.file_path)
        output = await remove_background(fbytes.read())
        await db.increment_processed(uid)
        result = BufferedInputFile(output, filename="magic.png")
        await message.answer_document(document=result, caption="Tayyor! Mana sizning rasmingiz")
        await status.delete()
    except Exception as e:
        logger.error(str(e))
        await status.edit_text("Xato yuz berdi. Qaytadan urinib ko'ring.")