"""Notification text templates (multi-language)."""
from __future__ import annotations


class NotificationTemplates:
    TEMPLATES = {
        "uz": {
            "welcome": "👋 Assalomu alaykum, {name}!\n\nMen sizning rasmlaringiz uchun professional yordamchiman:\n\n✂️ Fon o'chirish\n🎨 Orqa fon bilan ishlash\n🔍 Sifatni oshirish\n📄 Pasport fotosurati\n💎 Premium imkoniyatlar\n\nBoshlamoqchimisiz? Menyudan tanlang yoki rasm yuboring.",
            "daily_limit": "🚫 Bugungi limit tugadi ({limit} rasm).\n\n💎 Premium bilan cheksiz ishlov — /premium",
            "premium_activated": "✅ Premium faollashtirildi!\n\nTugash: {until}",
            "premium_expired": "⚠️ Premium muddati tugadi.\n\nYangilash: /premium",
            "support_reply": "💬 Support javobi:\n\n{text}",
            "broadcast": "📢 Yangilik:\n\n{text}",
        },
        "ru": {
            "welcome": "👋 Привет, {name}!\n\nЯ твой профессиональный помощник по изображениям:\n\n✂️ Удаление фона\n🎨 Замена фона\n🔍 Улучшение качества\n📄 Фото для паспорта\n💎 Premium возможности\n\nНачнём? Выбери пункт меню или отправь фото.",
            "daily_limit": "🚫 Дневной лимит исчерпан ({limit} фото).\n\n💎 Premium — безлимит: /premium",
            "premium_activated": "✅ Premium активирован!\n\nДействует до: {until}",
            "premium_expired": "⚠️ Premium истёк.\n\nПродлить: /premium",
            "support_reply": "💬 Ответ поддержки:\n\n{text}",
            "broadcast": "📢 Новость:\n\n{text}",
        },
        "en": {
            "welcome": "👋 Hello, {name}!\n\nI'm your professional image assistant:\n\n✂️ Background removal\n🎨 Background change\n🔍 Upscale\n📄 Passport photo\n💎 Premium features\n\nGet started — pick from the menu or send a photo.",
            "daily_limit": "🚫 Daily limit reached ({limit} images).\n\n💎 Premium for unlimited: /premium",
            "premium_activated": "✅ Premium activated!\n\nUntil: {until}",
            "premium_expired": "⚠️ Premium expired.\n\nRenew: /premium",
            "support_reply": "💬 Support reply:\n\n{text}",
            "broadcast": "📢 News:\n\n{text}",
        },
    }

    DEFAULT_LANG = "uz"

    @classmethod
    def get(cls, key: str, lang: str = "uz", **kwargs) -> str:
        lang = lang if lang in cls.TEMPLATES else cls.DEFAULT_LANG
        template = cls.TEMPLATES[lang].get(key) or cls.TEMPLATES[cls.DEFAULT_LANG].get(key, "")
        try:
            return template.format(**kwargs) if kwargs else template
        except Exception:
            return template

    @classmethod
    def welcome(cls, name: str, lang: str = "uz") -> str:
        return cls.get("welcome", lang, name=name)

    @classmethod
    def daily_limit_reached(cls, limit: int, lang: str = "uz") -> str:
        return cls.get("daily_limit", lang, limit=limit)

    @classmethod
    def premium_activated(cls, until: str, lang: str = "uz") -> str:
        return cls.get("premium_activated", lang, until=until)

    @classmethod
    def premium_expired(cls, lang: str = "uz") -> str:
        return cls.get("premium_expired", lang)


__all__ = ["NotificationTemplates"]