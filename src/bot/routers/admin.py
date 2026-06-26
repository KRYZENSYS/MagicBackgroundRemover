"""Admin router: stats, users, payments, broadcast, promo, plans, maintenance."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import get_admin_kb, get_confirm_kb
from src.bot.states import AdminFlow
from src.config.settings import settings
from src.services.admin.admin import AdminService
from src.services.admin.broadcast import BroadcastService
from src.services.admin.maintenance import maintenance_service
from src.services.analytics.analytics import AnalyticsService

admin_router = Router(name="admin")


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user if hasattr(event, "from_user") else None
        return user and user.id in settings.ADMIN_IDS


admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


@admin_router.message(Command("admin"))
@admin_router.callback_query(F.data == "menu:admin")
async def admin_home(event: Message | CallbackQuery):
    text = "🛠 <b>Admin panel</b>\n\nKerakli bo'limni tanlang:"
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_admin_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_admin_kb())


@admin_router.callback_query(F.data == "adm:stats")
async def adm_stats(call: CallbackQuery, session):
    svc = AdminService(session)
    stats = await svc.get_stats()
    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Users: <b>{stats['total_users']}</b>\n"
        f"   Bugun: <b>{stats['today_users']}</b>\n"
        f"   Hafta: <b>{stats['week_users']}</b>\n"
        f"   Premium: <b>{stats['premium_users']}</b>\n\n"
        f"🖼 Ishlangan: <b>{stats['total_processed']}</b>\n"
        f"   Bugun: <b>{stats['today_processed']}</b>\n\n"
        f"💰 Revenue: <b>{stats['total_revenue']:,.0f} so'm</b>\n"
        f"   Bugun: <b>{stats['today_revenue']:,.0f} so'm</b>\n\n"
        f"📈 Conversion: <b>{stats['conversion']:.1f}%</b>"
    )
    await call.message.edit_text(text, reply_markup=get_admin_kb())
    await call.answer()


@admin_router.callback_query(F.data == "adm:users")
async def adm_users(call: CallbackQuery, session):
    svc = AdminService(session)
    users = await svc.list_users(limit=20)
    lines = []
    for u in users:
        prem = "💎" if u.is_premium else "  "
        lines.append(f"{prem} {u.id} | @{u.username or '—'} | {u.first_name[:15]} | {u.total_processed}")
    text = "👥 <b>Oxirgi 20 foydalanuvchi</b>\n\n" + "\n".join(lines) if lines else "Hozircha user yo'q"
    await call.message.edit_text(text, reply_markup=get_admin_kb())
    await call.answer()


@admin_router.callback_query(F.data == "adm:payments")
async def adm_payments(call: CallbackQuery, session):
    svc = AdminService(session)
    payments = await svc.list_payments(limit=20)
    lines = []
    for p in payments:
        icon = {"completed": "✅", "pending": "⏳", "failed": "❌"}.get(p.status, "?")
        lines.append(f"{icon} {p.id} | {p.user_id} | {p.amount:,.0f} {p.currency} | {p.provider}")
    text = "💰 <b>Oxirgi 20 to'lov</b>\n\n" + "\n".join(lines) if lines else "Hozircha to'lov yo'q"
    await call.message.edit_text(text, reply_markup=get_admin_kb())
    await call.answer()


@admin_router.callback_query(F.data == "adm:broadcast")
async def adm_broadcast(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminFlow.broadcast_text)
    await call.message.edit_text(
        "📢 <b>Broadcast</b>\n\nYuboriladigan matnni yozing:\n\n/cancel — bekor qilish",
    )
    await call.answer()


@admin_router.message(AdminFlow.broadcast_text)
async def broadcast_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text or message.caption or "")
    await state.set_state(AdminFlow.broadcast_confirm)
    await message.answer(
        f"📢 Quyidagi matn yuboriladi:\n\n{message.text}\n\nTasdiqlaysizmi?",
        reply_markup=get_confirm_kb("broadcast"),
    )


@admin_router.callback_query(F.data == "confirm:broadcast", AdminFlow.broadcast_confirm)
async def broadcast_confirm(call: CallbackQuery, state: FSMContext, bot: Bot, session):
    data = await state.get_data()
    text = data.get("text", "")
    svc = BroadcastService(session, bot)
    sent, failed = await svc.broadcast_all(text)
    await call.message.edit_text(f"✅ Yuborildi: <b>{sent}</b>\n❌ Xato: <b>{failed}</b>")
    await state.clear()
    await call.answer()


@admin_router.callback_query(F.data == "confirm:cancel")
async def cancel_confirm(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi", reply_markup=get_admin_kb())
    await call.answer()


@admin_router.callback_query(F.data == "adm:promo")
async def adm_promo(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminFlow.promo_create)
    await call.message.edit_text(
        "🎫 <b>Promo kod yaratish</b>\n\nFormat:\n<code>CODE DAYS DISCOUNT%</code>\n\nMasalan: <code>SUMMER2026 7 0</code>",
    )
    await call.answer()


@admin_router.message(AdminFlow.promo_create)
async def promo_create(message: Message, state: FSMContext, session):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("❌ Format: <code>CODE DAYS [DISCOUNT%]</code>")
        return
    code = parts[0].upper()
    days = int(parts[1])
    discount = int(parts[2]) if len(parts) > 2 else 0
    svc = AdminService(session)
    promo = await svc.create_promo(code, days, discount, message.from_user.id)
    await message.answer(
        f"✅ Promo yaratildi:\n<code>{promo.code}</code>\n+{promo.bonus_days} kun, {promo.discount_percent}% chegirma",
    )
    await state.clear()


@admin_router.callback_query(F.data == "adm:plans")
async def adm_plans(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminFlow.plan_create)
    await call.message.edit_text(
        "💳 <b>Tarif yaratish</b>\n\nFormat:\n<code>CODE NAME PRICE DAYS CURRENCY</code>\n\nMasalan: <code>monthly Oylik 19900 30 UZS</code>",
    )
    await call.answer()


@admin_router.message(AdminFlow.plan_create)
async def plan_create(message: Message, state: FSMContext, session):
    parts = (message.text or "").split()
    if len(parts) < 5:
        await message.answer("❌ Format: <code>CODE NAME PRICE DAYS CURRENCY</code>")
        return
    code, name, price, days, currency = parts[0], parts[1], float(parts[2]), int(parts[3]), parts[4]
    svc = AdminService(session)
    plan = await svc.create_plan(code, name, price, days, currency)
    await message.answer(f"✅ Tarif yaratildi: <code>{plan.code}</code> — {plan.name}")
    await state.clear()


@admin_router.callback_query(F.data == "adm:analytics")
async def adm_analytics(call: CallbackQuery, session):
    svc = AnalyticsService(session)
    summary = await svc.summary(days=7)
    text = (
        f"📈 <b>Analytics (7 kun)</b>\n\n"
        f"📊 Events: <b>{summary['total_events']}</b>\n"
        f"👥 Active users: <b>{summary['active_users']}</b>\n"
        f"🖼 Tool uses: <b>{summary['tool_uses']}</b>\n\n"
        f"<b>Top tools:</b>\n"
    )
    for tool, count in summary.get("top_tools", [])[:5]:
        text += f"   {tool}: <b>{count}</b>\n"
    await call.message.edit_text(text, reply_markup=get_admin_kb())
    await call.answer()


@admin_router.callback_query(F.data == "adm:maintenance")
async def adm_maintenance(call: CallbackQuery):
    state = maintenance_service.is_on()
    text = f"🔧 Maintenance: {'✅ ON' if state else '❌ OFF'}"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔴 O'chirish" if state else "🟢 Yoqish",
            callback_data="maint:off" if state else "maint:on",
        )],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="menu:admin")],
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()


@admin_router.callback_query(F.data.startswith("maint:"))
async def toggle_maint(call: CallbackQuery):
    on = call.data.endswith(":on")
    maintenance_service.set(on)
    await call.message.edit_text(f"🔧 Maintenance {'yoqildi' if on else 'o'chirildi'}", reply_markup=get_admin_kb())
    await call.answer()


@admin_router.message(Command("ban"))
async def cmd_ban(message: Message, session):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("❌ Format: <code>/ban USER_ID [reason]</code>")
        return
    try:
        uid = int(parts[1])
    except ValueError:
        await message.answer("❌ USER_ID noto'g'ri")
        return
    reason = " ".join(parts[2:]) if len(parts) > 2 else ""
    svc = AdminService(session)
    await svc.ban_user(uid, reason)
    await message.answer(f"🚫 {uid} ban qilindi")


@admin_router.message(Command("unban"))
async def cmd_unban(message: Message, session):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("❌ Format: <code>/unban USER_ID</code>")
        return
    try:
        uid = int(parts[1])
    except ValueError:
        await message.answer("❌ USER_ID noto'g'ri")
        return
    svc = AdminService(session)
    await svc.unban_user(uid)
    await message.answer(f"✅ {uid} ban dan chiqarildi")


@admin_router.message(Command("givepremium"))
async def cmd_give_premium(message: Message, session):
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("❌ Format: <code>/givepremium USER_ID DAYS</code>")
        return
    try:
        uid, days = int(parts[1]), int(parts[2])
    except ValueError:
        await message.answer("❌ USER_ID/DAYS noto'g'ri")
        return
    svc = AdminService(session)
    await svc.give_premium(uid, days)
    await message.answer(f"✅ {uid} ga {days} kun premium berildi")


__all__ = ["admin_router"]