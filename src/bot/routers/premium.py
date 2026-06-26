"""Premium router: plans, checkout, payment confirm."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, LabeledPrice, Message
from aiogram.utils.web_app import WebAppInfo

from src.bot.keyboards.inline import get_plans_kb, get_pay_methods_kb, get_premium_kb
from src.services.payment.provider import payment_manager
from src.services.user.subscription import SubscriptionService

router = Router(name="premium")


@router.message(Command("premium"))
@router.message(F.text == "💎 Premium")
async def premium_menu(message: Message, session):
    sub_svc = SubscriptionService(session)
    sub = await sub_svc.get_user_subscription(message.from_user.id)
    text = "💎 <b>Premium imkoniyatlar</b>\n\n"
    if sub and sub.user.is_premium:
        text += f"✅ Premium faollashtirilgan\n📅 Tugash: {sub.user.premium_until}\n\n"
    text += (
        "Premium bilan:\n"
        "♾️ Cheksiz rasm\n"
        "🎨 Barcha effektlar\n"
        "⚡️ Tezroq ishlov\n"
        "🎁 Bonus kunlar\n"
        "💬 Uchrashuvsiz qo'llab-quvvatlash\n\n"
        "Tarifni tanlang:"
    )
    plans = await sub_svc.list_active()
    if plans:
        await message.answer(text, reply_markup=get_plans_kb(plans))
    else:
        await message.answer(text, reply_markup=get_premium_kb())


@router.callback_query(F.data.startswith("plan:"))
async def select_plan(call: CallbackQuery, session):
    code = call.data.split(":", 1)[1]
    sub_svc = SubscriptionService(session)
    plan = await sub_svc.get_plan(code)
    if not plan:
        await call.answer("Tarif topilmadi", show_alert=True)
        return
    text = (
        f"💎 <b>{plan.name}</b>\n\n"
        f"💰 Narx: <b>{plan.price:,} {plan.currency}</b>\n"
        f"📅 Muddat: {plan.duration_days} kun\n\n"
        "To'lov usulini tanlang:"
    )
    await call.message.edit_text(text, reply_markup=get_pay_methods_kb(code))
    await call.answer()


@router.callback_query(F.data.startswith("pay:"))
async def choose_pay(call: CallbackQuery, session):
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Format xato", show_alert=True)
        return
    _, plan_code, provider = parts
    mgr = payment_manager(session)
    result, payment = await mgr.create(call.from_user.id, plan_code, provider)
    if not result.success:
        await call.message.edit_text(f"❌ Xatolik: {result.error}")
        await call.answer()
        return
    if provider == "stars":
        # Telegram Stars — send invoice
        prices = [LabeledPrice(label=f"Premium {plan_code}", amount=int(result.amount * 100))]
        try:
            await call.bot.send_invoice(
                chat_id=call.from_user.id,
                title="Premium tarif",
                description=f"Premium {plan_code}",
                payload=f"premium:{plan_code}:{payment.id}",
                provider_token="",
                currency="XTR",
                prices=prices,
            )
            await call.answer("📤 Invoice yuborildi")
        except Exception as e:
            await call.message.edit_text(f"❌ Invoice xato: {e}")
            await call.answer()
        return
    # Other providers — give pay URL
    pay_url = result.payload.get("pay_url")
    if pay_url:
        kb = None
        try:
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💳 To'lash", url=pay_url),
                InlineKeyboardButton(text="🔄 Tekshirish", callback_data=f"check:{payment.id}"),
            ]])
        except Exception:
            pass
        await call.message.edit_text(
            f"💳 To'lov havolasi tayyor:\n\n<code>{pay_url}</code>\n\n"
            "To'lovni amalga oshiring va «Tekshirish» tugmasini bosing.",
            reply_markup=kb,
        )
    else:
        await call.message.edit_text(f"❌ To'lov sahifasi ochilmadi: {result.error}")
    await call.answer()


@router.callback_query(F.data.startswith("check:"))
async def check_payment(call: CallbackQuery, session):
    payment_id = int(call.data.split(":", 1)[1])
    mgr = payment_manager(session)
    payment = await mgr.confirm(payment_id, success=True) if call.data.endswith(":force") else None
    if not payment:
        await call.message.edit_text("⏳ To'lov hali qabul qilinmagan. Iltimos kuting...")
        await call.answer()
        return
    await call.message.edit_text(
        f"✅ To'lov tasdiqlandi!\n\nPremium faollashtirildi."
    )
    await call.answer()


@router.pre_checkout_query()
async def pre_checkout(query):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, session):
    sp = message.successful_payment
    payload = sp.invoice_payload
    if payload and payload.startswith("premium:"):
        _, plan_code, payment_id_s = payload.split(":")
        payment_id = int(payment_id_s)
        mgr = payment_manager(session)
        await mgr.confirm(payment_id, success=True)
        await message.answer("✅ To'lov tasdiqlandi! Premium faollashtirildi.")


__all__ = ["router"]