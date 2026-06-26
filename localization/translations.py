"""Localization — 3 languages: UZ, RU, EN."""
from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "uz": {
        "welcome": "👋 Salom, {name}!\n\n🤖 Men — MagicBackground Remover Pro\n\nRasm yuboring va orqa fonni o'chiraman, yoki kattalashtirib sifatni oshiraman.\n\nPremium — cheksiz imkoniyatlar! 💎",
        "help": "ℹ️ Yordam:\n\n• Rasm yuboring — BG o'chirish\n• /profile — Profil\n• /premium — Premium obuna\n• /referral — Referral\n• /language — Til",
        "choose_tool": "🎨 Qanday tool kerak?",
        "language_set": "✅ Til o'zgartirildi",
        "main_menu": "🏠 Asosiy menyu",
        "profile": "👤 Profil:\n\nIsm: {name}\nID: {telegram_id}\nUsername: {username}\nTil: {language}\nQo'shilgan: {joined}\n\n📊 Statistika:\nJami: {total} rasm\n\n💎 Premium: {premium}\nTugash: {until}\nTrial: {trial_used}\n\n👥 Referral:\nTaklif qildi: {referrer}\nTakliflar: {referral_count}",
        "settings": "⚙️ Sozlamalar",
        "premium_intro": "💎 Premium afzalliklari:\n\n✅ Cheksiz rasm\n✅ Yuqori sifat\n✅ Ultra HD\n✅ Passport foto\n✅ Barcha tool-lar\n✅ Tez ishlov",
        "processing": "⏳ Qayta ishlanmoqda...",
        "done": "✅ Tayyor!",
        "error": "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
        "limit_reached": "⚠️ Kunlik limit tugadi. Premium olib limitni oshiring!",
        "banned": "🚫 Siz bloklangansiz.",
        "referral_text": "👥 Referral:\n\nDo'stlarni taklif qiling va Premium oling!\n\nSizning havolangiz:\n{link}",
    },
    "ru": {
        "welcome": "👋 Привет, {name}!\n\n🤖 Я — MagicBackground Remover Pro\n\nОтправьте фото, и я удалю фон или улучшу качество.\n\nПремиум — безлимитные возможности! 💎",
        "help": "ℹ️ Помощь:\n\n• Отправьте фото — удаление фона\n• /profile — Профиль\n• /premium — Премиум\n• /referral — Реферал\n• /language — Язык",
        "choose_tool": "🎨 Какой инструмент нужен?",
        "language_set": "✅ Язык изменён",
        "main_menu": "🏠 Главное меню",
        "profile": "👤 Профиль:\n\nИмя: {name}\nID: {telegram_id}\nUsername: {username}\nЯзык: {language}\nРегистрация: {joined}\n\n📊 Статистика:\nВсего: {total}\n\n💎 Премиум: {premium}\nДо: {until}\nTrial: {trial_used}\n\n👥 Реферал:\nПригласил: {referrer}\nПриглашений: {referral_count}",
        "settings": "⚙️ Настройки",
        "premium_intro": "💎 Премиум возможности:\n\n✅ Безлимит изображений\n✅ Высокое качество\n✅ Ultra HD\n✅ Паспортное фото\n✅ Все инструменты\n✅ Быстрая обработка",
        "processing": "⏳ Обработка...",
        "done": "✅ Готово!",
        "error": "❌ Произошла ошибка. Попробуйте снова.",
        "limit_reached": "⚠️ Дневной лимит исчерпан. Оформите Премиум!",
        "banned": "🚫 Вы заблокированы.",
        "referral_text": "👥 Реферал:\n\nПриглашайте друзей и получайте Премиум!\n\nВаша ссылка:\n{link}",
    },
    "en": {
        "welcome": "👋 Hello, {name}!\n\n🤖 I'm — MagicBackground Remover Pro\n\nSend a photo and I'll remove the background or enhance quality.\n\nPremium — unlimited features! 💎",
        "help": "ℹ️ Help:\n\n• Send photo — Remove BG\n• /profile — Profile\n• /premium — Premium\n• /referral — Referral\n• /language — Language",
        "choose_tool": "🎨 Which tool?",
        "language_set": "✅ Language changed",
        "main_menu": "🏠 Main menu",
        "profile": "👤 Profile:\n\nName: {name}\nID: {telegram_id}\nUsername: {username}\nLanguage: {language}\nJoined: {joined}\n\n📊 Stats:\nTotal: {total}\n\n💎 Premium: {premium}\nUntil: {until}\nTrial: {trial_used}\n\n👥 Referral:\nInviter: {referrer}\nInvites: {referral_count}",
        "settings": "⚙️ Settings",
        "premium_intro": "💎 Premium features:\n\n✅ Unlimited images\n✅ High quality\n✅ Ultra HD\n✅ Passport photo\n✅ All tools\n✅ Fast processing",
        "processing": "⏳ Processing...",
        "done": "✅ Done!",
        "error": "❌ Error occurred. Try again.",
        "limit_reached": "⚠️ Daily limit reached. Get Premium!",
        "banned": "🚫 You are banned.",
        "referral_text": "👥 Referral:\n\nInvite friends and get Premium!\n\nYour link:\n{link}",
    },
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """Get translated text with placeholder substitution."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["uz"]).get(key, key)
    try:
        return text.format(**kwargs)
    except KeyError:
        return text