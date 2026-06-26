"""Referral and promo code handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database.engine import async_session
from database.repositories.user_repo import UserRepository
from database.repositories.payment_repo import PromoCodeRepository
from keyboards.inline import main_menu
from utils.helpers import build_referral_link
from localization import get_text

router = Router()


@router.message(F.text.in_(["👥 Referral", "👥 Реферал"]))
async def cmd_referral(message: Message):
    async with async_session() as session:
        user = await UserRepository(session).get(message.from_user.id)
        if not user:
            await message.answer("/start")
            return
        link = build_referral_link(user.telegram_id)
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Ulashish", url=f"https://t.me/share/url?url={link}")],
            [InlineKeyboardButton(text="🏆 Top", callback_data="referral_top")],
        ])
        await message.answer(
            get_text(user.language, "referral_text", link=link) +
            f"\n\n📊 Takliflaringiz: {user.referral_count}\n💰 Bonus: {user.referral_earnings}",
            reply_markup=kb,
        )


@router.callback_query(F.data == "referral_top")
async def callback_referral_top(callback: CallbackQuery):
    async with async_session() as session:
        top = await UserRepository(session).top_referrers(10)
    text = "🏆 Top referral:\n\n"
    for i, u in enumerate(top, 1):
        name = u.first_name or u.username or "Anonim"
        text += f"{i}. {name} — {u.referral_count}\n"
    await callback.message.answer(text or "Hozircha top yo'q")
    await callback.answer()


@router.message(F.text.startswith("🎫 "))
async def cmd_promo(message: Message):
    """Activate promo code."""
    code = message.text[3:].strip().upper()
    if not code:
        await message.answer("🎫 Promo kodni kiriting: `🎫 CODE`")
        return
    async with async_session() as session:
        promo_repo = PromoCodeRepository(session)
        promo = await promo_repo.get(code)
        if not promo:
            await message.answer("❌ Kod topilmadi")
            return
        success = await promo_repo.use(code)
        if success:
            user_repo = UserRepository(session)
            user = await user_repo.get(message.from_user.id)
            if user and promo.bonus_days > 0:
                from datetime import datetime, timedelta
                base = user.premium_until or datetime.utcnow()
                user.premium_until = base + timedelta(days=promo.bonus_days)
                user.premium = True
                await user_repo.session.commit()
                await message.answer(
                    f"✅ Kod qabul qilindi! +{promo.bonus_days} kun premium berildi."
                )
            else:
                await message.answer(f"✅ Kod qabul qilindi! Chegirma: {promo.discount_percent}%")
        else:
            await message.answer("❌ Kod eskirgan yoki limit tugagan")