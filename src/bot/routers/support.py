"""Support router: contact, FAQ, send to admins."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.config.logging import logger
from src.config.settings import settings

support_router = Router(name="support")


class SupportChat(StatesGroup):
    waiting_message = State()


@support_router.message(Command("support"))
@support_router.callback_query(F.data == "menu:support")
async def show_support(event: Message | CallbackQuery, state: FSMContext):
    await state.set_state(SupportChat.waiting_message)
    text = (
        "💬 <b>Support</b>\n\n"
        "Savolingizni yozing — adminlar tez orada javob beradi.\n\n"
        "Bekor qilish: /cancel"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text)
        await event.answer()
    else:
        await event.answer(text)


@support_router.message(SupportChat.waiting_message)
async def forward_support(message: Message, state: FSMContext, bot: Bot, db_user):
    user_info = (
        f"📨 <b>Yangi support xabar</b>\n\n"
        f"👤 {db_user.first_name} ({db_user.id})\n"
        f"📛 @{db_user.username or '—'}\n\n"
        f"💬 {message.text}"
    )
    sent = 0
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, user_info)
            sent += 1
        except Exception as e:
            logger.warning("Support forward to %s failed: %s", admin_id, e)
    if sent:
        await message.answer("✅ Xabaringiz yuborildi. Tez orada javob beramiz.")
    else:
        await message.answer("⚠️ Hozircha adminlar bilan bog'lanib bo'lmadi. Keyinroq urinib ko'ring.")
    await state.clear()


@support_router.callback_query(F.data == "menu:faq")
async def show_faq(call: CallbackQuery):
    text = (
        "❓ <b>FAQ</b>\n\n"
        "<b>1. Limit qancha?</b>\n"
        "Bepul: 5 rasm/kun. Premium: cheksiz.\n\n"
        "<b>2. Qanday to'layman?</b>\n"
        "Telegram Stars, Click, Payme, Stripe.\n\n"
        "<b>3. Premium qancha?</b>\n"
        "Oylik: 19900 so'm. Yillik: 179900 so'm.\n\n"
        "<b>4. Referral qanday ishlaydi?</b>\n"
        "Do'stni taklif qiling — ikkovingiz +7 kun premium olasiz.\n\n"
        "<b>5. Natijalar qayerda saqlanadi?</b>\n"
        "Telegram chatda. Serverda 24 soat.\n"
    )
    await call.message.edit_text(text, reply_markup=call.message.reply_markup)
    await call.answer()


__all__ = ["support_router"]