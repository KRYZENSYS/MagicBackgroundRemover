"""Premium subscription flow: plans -> provider -> invoice."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import get_payment_providers_kb, get_premium_plans_kb
from src.bot.states import PremiumFlow
from src.services.payment.manager import payment_manager
from src.services.user.subscription import SubscriptionService

premium_router = Router(name="premium")


@premium_router.message(Command("premium"))
@premium_router.callback_query(F.data == "menu:premium")
async def show_premium(event: Message | CallbackQuery, session, db_user):
    svc = SubscriptionService(session)
    plans = await svc.list_plans()
    plan_dicts = [
        {"code": p.code, "name": p.name, "price": p.price, "currency": p.currency}
        for p in plans
    ]
    text = (
        "💎 <b>Premium tariflar</b>\n\n"
        "Premium bilan:\n"
        "✅ Cheksiz rasm ishlov\n"
        "✅ Ultra HD sifat\n"
        "✅ Barcha effektlar\n"
        "✅ Tezkor navbat\n\n"
        "Quyidagidan tanlang:"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_premium_plans_kb(plan_dicts))
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_premium_plans_kb(plan_dicts))


@premium_router.callback_query(F.data.startswith("plan:"))
async def pick_plan(call: CallbackQuery, state: FSMContext):
    code = call.data.split(":", 1)[1]
    await state.update_data(plan_code=code)
    await call.message.edit_text(
        f"💳 <b>To'lov usulini tanlang</b>\n\nTarif: <code>{code}</code>",
        reply_markup=get_payment_providers_kb(code),
    )
    await call.answer()


@premium_router.callback_query(F.data.startswith("pay:"))
async def create_payment(call: CallbackQuery, state: FSMContext, bot, db_user):
    _, provider, plan_code = call.data.split(":")
    await state.update_data(plan_code=plan_code, provider=provider)
    result, payment = await payment_manager.create(db_user.id, plan_code, provider)
    if not result.success:
        await call.message.edit_text(f"❌ Xato: {result.error}\n\nQayta urinib ko'ring: /premium")
        await call.answer()
        return
    if provider == "stars":
        # Send Telegram Stars invoice
        try:
            await bot.send_invoice(
                chat_id=db_user.id,
                title=f"Premium ({plan_code})",
                description=f"Premium tarif: {plan_code}",
                payload=f"{db_user.id}:{plan_code}",
                provider_token="",
                currency="XTR",
                prices=[{"label": plan_code, "amount": int(result.amount)}],
            )
            await call.message.edit_text("✅ Invoice yuborildi. To'lovni yakunlang.")
        except Exception as e:
            await call.message.edit_text(f"❌ {e}")
    else:
        pay_url = (result.payload or {}).get("pay_url") or (result.payload or {}).get("invoice_id")
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 To'lov", url=pay_url)] if pay_url else [],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data=f"check:{payment.id if payment else 0}")],
        ].__class__([[InlineKeyboardButton(text="💳 To'lov", url=pay_url)] if pay_url else []]).union(None) if pay_url else InlineKeyboardMarkup())
        # Simpler build
        rows = []
        if pay_url:
            rows.append([InlineKeyboardButton(text="💳 To'lov qilish", url=pay_url)])
        rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=f"check:{payment.id if payment else 0}")])
        from aiogram.types import InlineKeyboardMarkup
        kb = InlineKeyboardMarkup(inline_keyboard=rows)
        await call.message.edit_text(
            f"💳 <b>To'lov havolasi</b>\n\nTarif: <code>{plan_code}</code>\nProvider: {provider}\n\nHavolani ochib to'lovni yakunlang.",
            reply_markup=kb,
        )
    await state.clear()
    await call.answer()


@premium_router.callback_query(F.data.startswith("check:"))
async def check_payment(call: CallbackQuery, db_user, session):
    payment_id = int(call.data.split(":")[1])
    from src.database.models.payment import Payment
    payment = await session.get(Payment, payment_id)
    if not payment:
        await call.answer("Topilmadi.", show_alert=True)
        return
    if payment.status == "completed":
        await call.message.edit_text("✅ To'lov tasdiqlandi! Premium faollashtirildi.")
        await call.answer()
        return
    if payment.status == "failed":
        await call.message.edit_text("❌ To'lov amalga oshmadi.")
        await call.answer()
        return
    await call.message.edit_text("⏳ To'lov hali tasdiqlanmagan. Bir ozdan keyin yana urinib ko'ring.")
    await call.answer()


@premium_router.message(Command("myplan"))
async def cmd_myplan(message: Message, db_user):
    if db_user.is_premium and db_user.premium_until:
        await message.answer(
            f"💎 Premium <b>faol</b>\nTugash: {db_user.premium_until:%d.%m.%Y}",
        )
    else:
        await message.answer("💎 Premium faol emas. /premium orqali faollashtiring.")


__all__ = ["premium_router"]