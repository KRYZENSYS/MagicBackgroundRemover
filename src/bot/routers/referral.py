"""Referral router: invite link, leaderboard."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline import get_referral_kb
from src.services.analytics.referral import ReferralService
from src.services.user.subscription import SubscriptionService

router = Router(name="referral")


@router.message(Command("referral"))
@router.message(F.text == "🎁 Referal")
async def referral_menu(message: Message, session):
    user_id = message.from_user.id
    username = (await message.bot.get_me()).username
    link = f"https://t.me/{username}?start=ref_{user_id}"
    sub_svc = SubscriptionService(session)
    sub = await sub_svc.get_user_subscription(user_id)
    count = sub.user.referral_count if sub else 0
    ref_svc = ReferralService(session)
    top = await ref_svc.top_referrers(limit=5)
    top_text = "\n".join(f"{i+1}. {u.first_name or '—'} — {c} 👥" for i, (u, c) in enumerate(top)) or "—"
    await message.answer(
        f"🎁 <b>Referal dasturi</b>\n\n"
        f"Do'st taklif qiling — ikkalangiz +7 kun premium oling!\n\n"
        f"Sizning linkingiz:\n<code>{link}</code>\n\n"
        f"📊 Takliflar: <b>{count}</b>\n\n"
        f"🏆 Top:\n{top_text}",
        reply_markup=get_referral_kb(),
    )


@router.callback_query(F.data == "ref:share")
async def ref_share(call: CallbackQuery):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    user_id = call.from_user.id
    username = (await call.bot.get_me()).username
    link = f"https://t.me/{username}?start=ref_{user_id}"
    await call.message.answer(
        f"🎁 Do'stlarga ulashing:\n\n<code>{link}</code>"
    )
    await call.answer()


@router.callback_query(F.data == "ref:top")
async def ref_top(call: CallbackQuery, session):
    ref_svc = ReferralService(session)
    top = await ref_svc.top_referrers(limit=10)
    lines = [f"{i+1}. {u.first_name or '—'} — {c} 👥" for i, (u, c) in enumerate(top)] or ["—"]
    await call.message.answer("🏆 Top referrers:\n\n" + "\n".join(lines))
    await call.answer()


__all__ = ["router"]