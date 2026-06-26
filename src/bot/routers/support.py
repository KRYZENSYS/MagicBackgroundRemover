"""Support router: FAQ, contact admin, ticket creation."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import get_support_kb
from src.database.models.support import SupportTicket
from src.database.session import async_session
from src.services.admin.admin import AdminService
from src.services.notification.scheduler import notification_scheduler

router = Router(name="support")


class SupportFlow(StatesGroup):
    question = State()


@router.message(Command("support"))
@router.message(F.text == "💬 Yordam")
async def support_menu(message: Message):
    await message.answer(
        "💬 <b>Yordam</b>\n\n"
        "Tez-tez beriladigan savollar:\n"
        "❓ Bot qanday ishlaydi?\n"
        "❓ Premium nima beradi?\n"
        "❓ To'lov qanday?\n\n"
        "Yoki savolingizni yozing:",
        reply_markup=get_support_kb(),
    )


@router.callback_query(F.data == "support:ask")
async def support_ask(call: CallbackQuery, state: FSMContext):
    await state.set_state(SupportFlow.question)
    await call.message.answer("✍️ Savolingizni yozing — adminlar tez orada javob beradi.")
    await call.answer()


@router.message(SupportFlow.question)
async def support_question(message: Message, state: FSMContext, session):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Iltimos matn yuboring.")
        return
    ticket = SupportTicket(
        user_id=message.from_user.id,
        question=text,
        status="open",
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    await message.answer(
        f"✅ Savol qabul qilindi! #{ticket.id}\n\n"
        "Admin javob berishi bilan xabar olasiz."
    )
    # Notify admins
    from src.config.settings import settings
    for admin_id in settings.ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🆕 Yangi support #{ticket.id}\n"
                f"👤 User: {message.from_user.id}\n"
                f"💬 {text[:200]}",
                reply_markup=get_support_kb(),
            )
        except Exception:
            pass
    await state.clear()


@router.callback_query(F.data.startswith("support:reply:"))
async def admin_reply(call: CallbackQuery, state: FSMContext, session):
    # Only for admins
    from src.config.settings import settings
    if call.from_user.id not in settings.ADMIN_IDS:
        await call.answer("Ruxsat yo'q", show_alert=True)
        return
    parts = call.data.split(":")
    ticket_id = int(parts[2])
    ticket = await session.get(SupportTicket, ticket_id)
    if not ticket:
        await call.answer("Topilmadi", show_alert=True)
        return
    from src.bot.states import AdminSupportReply
    await state.set_state(AdminSupportReply.ticket_id)
    await state.update_data(ticket_id=ticket_id)
    await call.message.answer(f"💬 Javob yozing #{ticket_id}:")
    await call.answer()


__all__ = ["router", "SupportFlow"]