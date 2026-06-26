"""Multilingual notification templates (UZ/RU/EN)."""
from __future__ import annotations


class NotificationTemplates:
    T = {
        "uz": {
            "welcome": "👋 Assalomu alaykum, {name}!\n\n🎨 Men — rasm fon o'chiruvchi bot.\nRasm yuboring — men avtomatik fonni o'chirib beraman.\n\n💎 Premium bilan cheksiz ishlang!",
            "daily_limit": "📊 Bugun limit tugadi: {limit}/{limit}\n\n💎 Premium bilan cheksiz ishlang:\n/premium",
            "premium_active": "💎 Premium faollashtirildi!\n⏳ Tugash: {date}",
            "premium_expired": "⚠️ Premium tugadi. Yangilang: /premium",
            "payment_success": "✅ To'lov tasdiqlandi!\n💎 Premium berildi: {days} kun",
            "referral_invite": "🎁 Sizning linkingiz:\n{link}\n\nDo'st taklif qiling — ikkovingiz +7 kun premium oling!",
            "new_feature": "🆕 Yangi funksiya: {name}\n\n{description}",
        },
        "ru": {
            "welcome": "👋 Привет, {name}!\n\n🎨 Я — бот для удаления фона с изображений.\nОтправь фото — я автоматически уберу фон.\n\n💎 С Premium без лимитов!",
            "daily_limit": "📊 Лимит на сегодня исчерпан: {limit}/{limit}\n\n💎 С Premium без ограничений:\n/premium",
            "premium_active": "💎 Premium активирован!\n⏳ До: {date}",
            "premium_expired": "⚠️ Premium истек. Продлить: /premium",
            "payment_success": "✅ Оплата подтверждена!\n💎 Premium: {days} дней",
            "referral_invite": "🎁 Ваша ссылка:\n{link}\n\nПригласите друга — оба получите +7 дней Premium!",
            "new_feature": "🆕 Новая функция: {name}\n\n{description}",
        },
        "en": {
            "welcome": "👋 Hi, {name}!\n\n🎨 I'm a background removal bot.\nSend me a photo — I'll auto-remove its background.\n\n💎 Unlimited with Premium!",
            "daily_limit": "📊 Daily limit reached: {limit}/{limit}\n\n💎 Get unlimited with Premium:\n/premium",
            "premium_active": "💎 Premium activated!\n⏳ Until: {date}",
            "premium_expired": "⚠️ Premium expired. Renew: /premium",
            "payment_success": "✅ Payment confirmed!\n💎 Premium: {days} days",
            "referral_invite": "🎁 Your invite link:\n{link}\n\nInvite a friend — you both get +7 days Premium!",
            "new_feature": "🆕 New feature: {name}\n\n{description}",
        },
    }

    @classmethod
    def _tr(cls, key: str, lang: str, **kwargs) -> str:
        bundle = cls.T.get(lang, cls.T["uz"])
        template = bundle.get(key, cls.T["uz"].get(key, key))
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    @classmethod
    def welcome(cls, name: str, lang: str = "uz") -> str:
        return cls._tr("welcome", lang, name=name)

    @classmethod
    def daily_limit_reached(cls, limit: int, lang: str = "uz") -> str:
        return cls._tr("daily_limit", lang, limit=limit)

    @classmethod
    def premium_active(cls, date: str, lang: str = "uz") -> str:
        return cls._tr("premium_active", lang, date=date)

    @classmethod
    def premium_expired(cls, lang: str = "uz") -> str:
        return cls._tr("premium_expired", lang)

    @classmethod
    def payment_success(cls, days: int, lang: str = "uz") -> str:
        return cls._tr("payment_success", lang, days=days)

    @classmethod
    def referral_invite(cls, link: str, lang: str = "uz") -> str:
        return cls._tr("referral_invite", lang, link=link)

    @classmethod
    def new_feature(cls, name: str, description: str, lang: str = "uz") -> str:
        return cls._tr("new_feature", lang, name=name, description=description)


__all__ = ["NotificationTemplates"]