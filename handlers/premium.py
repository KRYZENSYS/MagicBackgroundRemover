"""Premium subscription and payment handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice

from core.settings import settings
from core.logger import logger
from database.engine import async_session
from database.repositories.user_repo import UserRepository
from database.repositories.payment_repo import PlanRepository, PaymentRepository
from services.payment import PaymentService
from keyboards.inline import premium_plans, payment_methods
from localization import get_text

router = Router()


@router.message(F.text.in_(["💎 Premium", "💎 Премиум"]))
async def cmd_premium(message: Message):
    async with async_session() as session:
        plan_repo = PlanRepository(session)
        plans = await plan_repo.list_active()
        await message.answer(
            get_text("uz", "premium_intro"),
            reply_markup=premium_plans(plans),
        )


@router.callback_query(F.data.startswith("plan_"))
async def callback_plan(callback: CallbackQuery):
    plan_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        plan = await PlanRepository(session).get(plan_id)
        if not plan:
            await callback.answer("Plan not found")
            return
        await callback.message.edit_text(
            f"\ud83d\udcb3 To'lov usulini tanlang:\n\n{plan.name} — {plan.price} {plan.currency}",
            reply_markup=payment_methods(plan.id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_telegram_"))
async def callback_pay_telegram(callback: CallbackQuery):
    plan_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        plan = await PlanRepository(session).get(plan_id)
        if not plan:
            return
        prices = [LabeledPrice(label=plan.name, amount=int(plan.price * 100))]
        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title=plan.name,
            description=f"Subscription: {plan.duration_days} days",
            payload=f"plan_{plan_id}",
            provider_token=settings.PAYMENT_PROVIDER_TOKEN or "",
            currency=plan.currency,
            prices=prices,
        )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    payload_parts = payment.invoice_payload.split("_")
    plan_id = int(payload_parts[1])
    async with async_session() as session:
        payment_repo = PaymentRepository(session)
        user_repo = UserRepository(session)
        plan = await PlanRepository(session).get(plan_id)
        # Record payment
        pay = await payment_repo.create(
            user_id=message.from_user.id,
            plan_id=plan_id,
            amount=plan.price,
            provider="telegram_stars",
            transaction_id=payment.telegram_payment_charge_id,
        )
        await payment_repo.complete(pay.id)
        # Activate premium
        await user_repo.set_premium(message.from_user.id, plan.duration_days)
        await message.answer(
            f"\u2705 Premium faollashtirildi!\n"
            f"Muddati: {plan.duration_days} kun\n"
            f"To'lov: {plan.price} {plan.currency}"
        )