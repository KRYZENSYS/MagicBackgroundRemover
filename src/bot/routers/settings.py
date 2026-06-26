"""User settings router (language, notifications, data export)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import get_settings_kb
from src.services.user.subscription import SubscriptionService

router = Router(name="settings")


@router.message(F.text == "⚙️ Sozlamalar")
@router.message(F.text == "/settings")
async def settings_menu(message: Message, session):
    sub_svc = SubscriptionService(session)
    sub = await sub_svc.get_user_subscription(message.from_user.id)
    lang = sub.user.language if sub else "uz"
    notif = "✅" if (sub and sub.user.notifications_enabled) else "❌"
    await message.answer(
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"🌐 Til: {lang}\n"
        f"🔔 Bildirishnomalar: {notif}\n\n",
        reply_markup=get_settings_kb(),
    )


@router.callback_query(F.data == "settings:notifications")
async def toggle_notifications(call: CallbackQuery, session):
    sub_svc = SubscriptionService(session)
    sub = await sub_svc.get_user_subscription(call.from_user.id)
    if sub:
        sub.user.notifications_enabled = not sub.user.notifications_enabled
        await session.commit()
        status = "✅ Yoqildi" if sub.user.notifications_enabled else "❌ O'chirildi"
        await call.answer(status, show_alert=True)
        await call.message.edit_reply_markup(reply_markup=get_settings_kb())


@router.callback_query(F.data == "settings:export")
async def export_data(call: CallbackQuery, session):
    from src.services.user.subscription import SubscriptionService
    sub_svc = SubscriptionService(session)
    sub = await sub_svc.get_user_subscription(call.from_user.id)
    if not sub:
        await call.answer("Ma'lumot topilmadi", show_alert=True)
        return
    text = (
        f"📊 <b>Sizning ma'lumotlaringiz</b>\n\n"
        f"ID: <code>{sub.user.id}</code>\n"
        f"Ism: {sub.user.first_name or '—'}\n"
        f"Username: @{sub.user.username or '—'}\n"
        f"Til: {sub.user.language}\n"
        f"Jami rasmlar: {sub.user.total_processed}\n"
        f"Premium: {'✅' if sub.user.is_premium else '❌'}\n"
        f"Premium tugash: {sub.user.premium_until or '—'}\n"
    )
    await call.message.answer(text)
    await call.answer()


__all__ = ["router"]