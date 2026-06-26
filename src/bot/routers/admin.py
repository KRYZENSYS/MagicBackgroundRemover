"""Admin panel: stats, users, broadcast, promo, plans, ban, payments."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import get_admin_kb, get_confirm_kb
from src.bot.states import AdminFlow
from src.config.settings import settings
from src.services.admin.admin import AdminService
from src.services.notification.scheduler import notification_scheduler

admin_router = Router(name="admin")


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return bool(user and user.id in settings.ADMIN_IDS)


admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


@admin_router.message(Command("admin"))
@admin_router.callback_query(F.data == "menu:admin")
async def admin_home(event: Message | CallbackQuery, session):
    svc = AdminService(session)
    stats = await svc.quick_stats()
    text = (
        "🛠 <b>Admin panel</b>\n\n"
        f"👥 Users: <b>{stats['users']}</b>\n"
        f"📈 Today: <b>{stats['today_new']}</b>\n"
        f"💎 Premium: <b>{stats['premium']}</b>\n"
        f"💰 Revenue: <b>{stats['revenue']:,}</b>\n"
        f"📊 Today ops: <b>{stats['today_ops']}</b>\n"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_admin_kb())
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_admin_kb())


@admin_router.callback_query(F.data == "adm:stats")
async def admin_stats(call: CallbackQuery, session):
    svc = AdminService(session)
    s = await svc.deep_stats()
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Users total: {s['users_total']}\n"
        f"🆕 Today: {s['users_today']}\n"
        f"📅 Week: {s['users_week']}\n"
        f"📅 Month: {s['users_month']}\n\n"
        f"💎 Premium users: {s['premium_total']}\n"
        f"💰 Revenue total: {s['revenue_total']:,}\n"
        f"💰 Today: {s['revenue_today']:,}\n\n"
        f"📈 Ops total: {s['ops_total']}\n"
        f"📈 Today: {s['ops_today']}\n"
        f"⚡ Avg latency: {s.get('avg_latency_ms', 0):.0f}ms\n\n"
        f"🛠 Tool usage:\n" + "\n".join(f"   • {k}: {v}" for k, v in s.get('top_tools', []))
    )
    await call.message.edit_text(text, reply_markup=get_admin_kb())
    await call.answer()


@admin_router.callback_query(F.data == "adm:users")
async def admin_users(call: CallbackQuery, session):
    svc = AdminService(session)
    await call.message.edit_text(
        "👥 <b>Users</b>\n\nID yoki username yuboring:",
        reply_markup=None,
    )
    await state_set(call, AdminFlow.user_search)
    await call.answer()


async def state_set(call: CallbackQuery, state: FSMContext):
    pass  # placeholder; actual state set in handler


@admin_router.message(AdminFlow.user_search)
async def admin_user_search(message: Message, state: FSMContext, session):
    query = (message.text or "").strip()
    svc = AdminService(session)
    users = await svc.search_users(query, limit=10)
    if not users:
        await message.answer("❌ Topilmadi.")
        return
    lines = [f"• <code>{u.id}</code> {u.first_name or '—'} (@{u.username or '—'}) — premium={u.is_premium}" for u in users]
    await message.answer("\n".join(lines))


@admin_router.callback_query(F.data == "adm:broadcast")
async def admin_broadcast(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminFlow.broadcast_text)
    await call.message.edit_text("📢 Broadcast xabari yuboring (matn yoki rasm):")
    await call.answer()


@admin_router.message(AdminFlow.broadcast_text)
async def admin_broadcast_received(message: Message, state: FSMContext, session):
    if message.text:
        AdminFlow.broadcast_text  # noqa
        from src.services.admin.broadcast import BroadcastService
        svc = BroadcastService(session)
        count = await svc.queue_broadcast(message.text)
        await message.answer(f"📤 Broadcast navbatga qo'shildi. Qabul qiluvchilar: ~{count}\n\nYuborishni tasdiqlaysizmi?", reply_markup=get_confirm_kb(f"broadcast:{count}"))
    else:
        await message.answer("Iltimos matn yuboring.")


@admin_router.callback_query(F.data.startswith("confirm:broadcast:"))
async def confirm_broadcast(call: CallbackQuery, session):
    from src.services.admin.broadcast import BroadcastService
    svc = BroadcastService(session)
    started = await svc.start_pending()
    await call.message.edit_text(f"✅ Broadcast yuborish boshlandi (≈{started} ta).")
    await call.answer()


@admin_router.callback_query(F.data == "adm:promo")
async def admin_promo(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminFlow.promo_create)
    await call.message.edit_text(
        "🎫 Promo yaratish.\n\n"
        "Format: <code>CODE,DAYS,DISCOUNT,LIMIT</code>\n"
        "Misol: <code>SUMMER2026,7,0,100</code>"
    )
    await call.answer()


@admin_router.message(AdminFlow.promo_create)
async def admin_promo_create(message: Message, state: FSMContext, session):
    from src.services.admin.promo import PromoAdminService
    parts = (message.text or "").strip().split(",")
    if len(parts) < 2:
        await message.answer("❌ Format: CODE,DAYS,DISCOUNT,LIMIT")
        return
    code = parts[0].strip().upper()
    days = int(parts[1].strip() or "0")
    discount = int(parts[2].strip() or "0") if len(parts) > 2 else 0
    limit = int(parts[3].strip() or "100") if len(parts) > 3 else 100
    svc = PromoAdminService(session)
    promo = await svc.create(code, days, discount, limit)
    await message.answer(f"✅ Promo yaratildi: <code>{promo.code}</code>")
    await state.clear()


@admin_router.callback_query(F.data == "adm:plans")
async def admin_plans(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminFlow.plan_create)
    await call.message.edit_text(
        "💰 Tarif yaratish.\n\n"
        "Format: <code>CODE,NAME,PRICE,CURRENCY,DAYS</code>\n"
        "Misol: <code>monthly,Oylik,19900,UZS,30</code>"
    )
    await call.answer()


@admin_router.message(AdminFlow.plan_create)
async def admin_plan_create(message: Message, state: FSMContext, session):
    parts = (message.text or "").strip().split(",")
    if len(parts) < 5:
        await message.answer("❌ Format: CODE,NAME,PRICE,CURRENCY,DAYS")
        return
    from src.services.admin.plan_admin import PlanAdminService
    svc = PlanAdminService(session)
    plan = await svc.create(
        code=parts[0].strip(),
        name=parts[1].strip(),
        price=int(parts[2].strip()),
        currency=parts[3].strip().upper(),
        duration_days=int(parts[4].strip()),
    )
    await message.answer(f"✅ Tarif: <b>{plan.name}</b> ({plan.price} {plan.currency})")
    await state.clear()


@admin_router.callback_query(F.data == "adm:payments")
async def admin_payments(call: CallbackQuery, session):
    from src.services.admin.admin import AdminService
    svc = AdminService(session)
    payments = await svc.recent_payments(limit=20)
    if not payments:
        await call.message.edit_text("💰 To'lovlar yo'q.", reply_markup=get_admin_kb())
        await call.answer()
        return
    lines = [f"• #{p.id} {p.amount} {p.currency} — {p.status} — {p.user_id} — {p.created_at:%d.%m %H:%M}" for p in payments]
    await call.message.edit_text("💰 <b>So'nggi to'lovlar</b>\n\n" + "\n".join(lines), reply_markup=get_admin_kb())
    await call.answer()


@admin_router.callback_query(F.data == "adm:analytics")
async def admin_analytics(call: CallbackQuery, session):
    from src.services.admin.admin import AdminService
    svc = AdminService(session)
    a = await svc.analytics_30d()
    text = (
        "📈 <b>30 kunlik analitika</b>\n\n"
        f"DAU: {a['dau']}\n"
        f"WAU: {a['wau']}\n"
        f"MAU: {a['mau']}\n\n"
        f"Retention D1: {a['retention_d1']}%\n"
        f"Retention D7: {a['retention_d7']}%\n\n"
        f"Conversion to premium: {a['conversion']}%\n"
        f"ARPU: {a['arpu']}\n"
        f"LTV estimate: {a['ltv']}\n"
    )
    await call.message.edit_text(text, reply_markup=get_admin_kb())
    await call.answer()


@admin_router.callback_query(F.data == "adm:maintenance")
async def admin_maint(call: CallbackQuery, session):
    from src.services.admin.admin import AdminService
    svc = AdminService(session)
    current = await svc.get_setting("maintenance_mode", "off")
    new = "off" if current == "on" else "on"
    await svc.set_setting("maintenance_mode", new)
    await call.message.edit_text(f"🔧 Maintenance: <b>{new.upper()}</b>", reply_markup=get_admin_kb())
    await call.answer()


@admin_router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    await state.set_state(AdminFlow.broadcast_text)
    await message.answer("📢 Broadcast matni yuboring:")


@admin_router.message(Command("stats"))
async def cmd_stats(message: Message, session):
    svc = AdminService(session)
    s = await svc.deep_stats()
    await message.answer(f"Users: {s['users_total']}\nToday: {s['users_today']}\nRevenue: {s['revenue_total']:,}")


__all__ = ["admin_router"]