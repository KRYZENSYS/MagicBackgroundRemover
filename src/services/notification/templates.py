"""Notification message templates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class NotificationTemplates:
    """i18n-ready templates. Keys are stable; values can be replaced via i18n files later."""

    WELCOME_UZ = (
        "🎉 Xush kelibsiz, {first_name}!\n\n"
        "Men — <b>MagicBackground Remover</b> 🤖\n"
        "Rasmlaringiz fonini 1 soniyada o'chirib beraman.\n\n"
        "🚀 Boshlash uchun /help buyrug'ini yuboring."
    )
    WELCOME_RU = (
        "🎉 Добро пожаловать, {first_name}!\n\n"
        "Я — <b>MagicBackground Remover</b> 🤖\n"
        "Удаляю фон с фото за 1 секунду.\n\n"
        "🚀 Чтобы начать, отправьте /help."
    )
    WELCOME_EN = (
        "🎉 Welcome, {first_name}!\n\n"
        "I'm <b>MagicBackground Remover</b> 🤖\n"
        "I remove photo backgrounds in 1 second.\n\n"
        "🚀 Send /help to get started."
    )

    PREMIUM_EXPIRING_UZ = (
        "⏳ <b>Premium obuna tugayapti!</b>\n\n"
        "Sizning premium obnangiz <b>{days_left}</b> kun ichida tugaydi.\n"
        "Davom ettirish uchun /premium bosing."
    )
    PREMIUM_EXPIRING_RU = (
        "⏳ <b>Премиум-подписка скоро истекает!</b>\n\n"
        "Ваша премиум-подписка истекает через <b>{days_left}</b> дн.\n"
        "Продлить: /premium."
    )

    PREMIUM_EXPIRED_UZ = (
        "🔔 Premium obna tugadi.\n"
        "Cheksiz ishlash uchun qayta faollashtiring: /premium"
    )

    PAYMENT_SUCCESS_UZ = (
        "✅ <b>To'lov muvaffaqiyatli!</b>\n\n"
        "Sizning premium obnangiz faollashtirildi.\n"
        "Imkoniyatlardan to'liq foydalaning!"
    )
    PAYMENT_SUCCESS_RU = (
        "✅ <b>Оплата прошла успешно!</b>\n\n"
        "Премиум-подписка активирована.\n"
        "Пользуйтесь всеми возможностями!"
    )

    DAILY_LIMIT_REACHED_UZ = (
        "🚫 Bugungi limit tugadi ({limit} ta).\n"
        "Premium obna bilan cheksiz ishlang: /premium"
    )

    REFERRAL_INVITED_UZ = (
        "🎁 Sizni <b>{inviter_name}</b> taklif qildi!\n\n"
        "Bonus sifatida <b>{days}</b> kunlik premium berildi.\n"
        "Sizning referral linkingiz: <code>{link}</code>"
    )

    @staticmethod
    def welcome(first_name: str, lang: str = "uz") -> str:
        t = getattr(NotificationTemplates, f"WELCOME_{lang.upper()}", NotificationTemplates.WELCOME_UZ)
        return t.format(first_name=first_name or "do'st")

    @staticmethod
    def premium_expiring(days_left: int, lang: str = "uz") -> str:
        t = getattr(NotificationTemplates, f"PREMIUM_EXPIRING_{lang.upper()}", NotificationTemplates.PREMIUM_EXPIRING_UZ)
        return t.format(days_left=days_left)

    @staticmethod
    def premium_expired(lang: str = "uz") -> str:
        t = getattr(NotificationTemplates, f"PREMIUM_EXPIRED_{lang.upper()}", NotificationTemplates.PREMIUM_EXPIRED_UZ)
        return t

    @staticmethod
    def payment_success(lang: str = "uz") -> str:
        t = getattr(NotificationTemplates, f"PAYMENT_SUCCESS_{lang.upper()}", NotificationTemplates.PAYMENT_SUCCESS_UZ)
        return t

    @staticmethod
    def daily_limit_reached(limit: int, lang: str = "uz") -> str:
        t = getattr(NotificationTemplates, f"DAILY_LIMIT_REACHED_{lang.upper()}", NotificationTemplates.DAILY_LIMIT_REACHED_UZ)
        return t.format(limit=limit)


__all__ = ["NotificationTemplates"]