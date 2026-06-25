"""Konfiguratsiya"""
import os
from pathlib import Path

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [123456789]
ADMIN_USERNAME = "your_admin"

REQUIRED_CHANNELS = ["@your_channel"]

BOT_NAME = "MagicBackground Remover"
BOT_USERNAME = "@BgGoneBot"
BOT_VERSION = "1.0.0"

FREE_DAILY_LIMIT = 5
PREMIUM_DAILY_LIMIT = 100

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
DATABASE_DIR = BASE_DIR / "database"
LOGS_DIR = BASE_DIR / "logs"
DATABASE_PATH = DATABASE_DIR / "bot.db"

REMBG_MODEL = "u2net"

MESSAGES = {
    "uz": {
        "welcome": "Salom, {name}!\n\nMagicBackground Remover botiga xush kelibsiz.\nRasm yuboring - orqa foni avtomatik o'chiriladi.",
        "send_photo": "Rasm yuboring",
        "processing": "O'chirilmoqda...",
        "done": "Tayyor!",
        "error": "Xato yuz berdi",
        "limit_reached": "Kunlik limit tugadi ({limit})",
        "must_subscribe": "Kanalga obuna bo'ling",
        "subscribed": "Obuna tasdiqlandi",
        "referral_invite": "Havolangiz:\n{link}\n\nTaklif qilganlar: {count}"
    },
    "ru": {
        "welcome": "Привет, {name}!\n\nДобро пожаловать в MagicBackground Remover.",
        "send_photo": "Отправьте фото",
        "processing": "Обработка...",
        "done": "Готово!",
        "error": "Ошибка",
        "limit_reached": "Лимит ({limit})",
        "must_subscribe": "Подпишитесь",
        "subscribed": "Подписка подтверждена",
        "referral_invite": "Ссылка:\n{link}\n\nПриглашено: {count}"
    },
    "en": {
        "welcome": "Hello, {name}!\n\nWelcome to MagicBackground Remover.",
        "send_photo": "Send a photo",
        "processing": "Processing...",
        "done": "Done!",
        "error": "Error",
        "limit_reached": "Limit reached ({limit})",
        "must_subscribe": "Please subscribe",
        "subscribed": "Subscribed",
        "referral_invite": "Your link:\n{link}\n\nInvited: {count}"
    }
}

DEFAULT_LANGUAGE = "uz"