"""Promo code router."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.services.analytics.referral import ReferralService

router = Router(name="promo")


class PromoFlow(StatesGroup):
    code = State()


@router.message(Command("promo"))
async def promo_cmd(message: Message, state: FSMContext):
    await state.set_state(PromoFlow.code)
    await message.answer("🎫 Promo kodni yuboring:")


@router.message(PromoFlow.code)
async def promo_apply(message: Message, state: FSMContext, session):
    code = (message.text or "").strip().upper()
    if not code:
        await message.answer("❌ Bo'sh kod")
        return
    ref_svc = ReferralService(session)
    try:
        promo = await ref_svc.redeem_promo(code, message.from_user.id)
    except ValueError as e:
        await message.answer(f"❌ {e}")
        await state.clear()
        return
    bonus = ""
    if promo.bonus_days > 0:
        bonus = f"\n\n🎁 +{promo.bonus_days} kun premium berildi!"
    await message.answer(f"✅ Promo kod qabul qilindi!<code>{promo.code}</code>{bonus}")
    await state.clear()


__all__ = ["router", "PromoFlow"]