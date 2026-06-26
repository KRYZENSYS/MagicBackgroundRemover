"""Referral and promo-code handlers."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import get_main_menu_kb
from src.services.analytics.referral import ReferralService

referral_router = Router(name="referral")


@referral_router.message(Command("referral"))
@referral_router.callback_query(F.data == "menu:referral")
async def show_referral(event: Message | CallbackQuery, db_user, bot, session):
    bot_username = (await bot.me()).username
    link = f"https://t.me/{bot_username}?start=ref_{db_user.id}"
    text = (
        "👥 <b>Referral tizimi</b>\n\n"
        f"Do'stlarni taklif qiling va har biri uchun <b>+7 kun premium</b> oling.\n\n"
        f"🔗 Sizning linkingiz:\n<code>{link}</code>\n\n"
        f"📊 Takliflar: <b>{db_user.referral_count}</b>"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Ulashish", url=f"https://t.me/share/url?url={link}")],
        [InlineKeyboardButton(text="🏆 Top", callback_data="ref:top")],
        [InlineKeyboardButton(text="◀️ Menyu", callback_data="menu:main")],
    ])
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb)


@referral_router.callback_query(F.data == "ref:top")
async def top_referrers(call: CallbackQuery, session):
    svc = ReferralService(session)
    top = await svc.top_referrers(10)
    if not top:
        await call.answer("Hozircha top yo'q", show_alert=True)
        return
    lines = []
    for i, (u, count) in enumerate(top, 1):
        name = (u.first_name or u.username or "Foydalanuvchi")[:20]
        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else "  "
        lines.append(f"{medal} {i}. {name} — <b>{count}</b>")
    await call.message.edit_text("🏆 <b>Top referral</b>\n\n" + "\n".join(lines))
    await call.answer()


@referral_router.message(Command("promo"))
async def cmd_promo(message: Message, session, db_user):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("🎫 Promo kodni kiriting:\n<code>/promo CODE</code>")
        return
    code = parts[1].strip().upper()
    svc = ReferralService(session)
    try:
        promo = await svc.redeem_promo(code, db_user.id)
        days = promo.bonus_days
        discount = promo.discount_percent
        if days > 0:
            await message.answer(f"✅ Kod qabul qilindi! +{days} kun premium berildi.")
        elif discount > 0:
            await message.answer(f"✅ Kod qabul qilindi! {discount}% chegirma.")
        else:
            await message.answer("✅ Kod faollashtirildi.")
    except Exception as e:
        await message.answer(f"❌ {e}")


__all__ = ["referral_router"]