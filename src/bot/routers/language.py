"""Language selection router."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from src.bot.keyboards.inline import get_lang_kb
from src.services.user.subscription import SubscriptionService

router = Router(name="language")


@router.callback_query(F.data == "menu:language")
async def language_menu(call: CallbackQuery):
    await call.message.edit_text(
        "🌐 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=get_lang_kb(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("lang:"))
async def language_set(call: CallbackQuery, session):
    code = call.data.split(":", 1)[1]
    if code not in ("uz", "ru", "en"):
        await call.answer("Noto'g'ri til")
        return
    sub_svc = SubscriptionService(session)
    await sub_svc.set_language(call.from_user.id, code)
    await call.answer("✅ Saqlandi")
    await call.message.edit_text(
        {"uz": "🇺🇿 O'zbek tili tanlandi.",
         "ru": "🇷🇺 Русский выбран.",
         "en": "🇬🇧 English selected."}[code]
    )


__all__ = ["router"]