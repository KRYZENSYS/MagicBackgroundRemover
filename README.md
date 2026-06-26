# ✨ MagicBackgroundRemover

> Professional Telegram bot for AI-powered image processing.
> Background removal, upscaling, face enhancement, passport photos, and more.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-%40MagicBgBot-blue)](https://t.me/MagicBgBot)

---

## 🎯 Features

### Image tools (free + premium)
- ✂️ **Background removal** — U-2-Net / rembg / ISNet
- 🎨 **Background replacement** — solid color, gradient, custom image
- 🔍 **Upscaling** — Real-ESRGAN 2x / 4x
- ✨ **Auto-enhance** — sharpness, contrast, color
- 👤 **Face enhancement** — GFPGAN
- 📄 **Passport / ID photo** — auto-crop + white background
- 🌑 **Drop shadow** — for product photos
- 🔖 **Watermark** — text overlay
- 📐 **Crop / Resize / Rotate / Flip**
- 🔄 **Format conversion** — PNG/JPG/WEBP/PDF

### Business features
- 💎 **Subscriptions** — monthly, yearly, lifetime
- 💳 **Multi-provider payments** — Click, Payme, Stripe, Telegram Stars, Crypto
- 🎁 **Referral program** — both referrer and referee get +7 days Premium
- 🎫 **Promo codes** — admin-creatable, with usage limits
- 📊 **Admin dashboard** — stats, broadcasts, user search, payments
- 🌐 **Multi-language** — UZ, RU, EN (auto-detected)
- 🔔 **Notifications** — premium expiry reminders, daily digests
- 📈 **Analytics** — events, counters, retention metrics
- 🛡 **Maintenance mode** — toggle via /admin
- 🎯 **Sentry** error tracking
- 🐳 **Docker** + **docker-compose** for one-line deploy

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/KRYZENSYS/MagicBackgroundRemover.git
cd MagicBackgroundRemover
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure `.env`

```bash
# Required
BOT_TOKEN=...
ADMIN_IDS=123456789
DATABASE_URL=postgresql+asyncpg://magic:bg@db:5432/magicdb

# Optional (payments)
CLICK_MERCHANT_ID=...
CLICK_SECRET=...
PAYME_MERCHANT_ID=...
PAYME_KEY=...
STRIPE_SECRET_KEY=...
NOWPAYMENTS_API_KEY=...
```

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Start the bot

```bash
python -m src.main
```

Or with Docker:
```bash
docker-compose up -d
```

---

## 🏗 Architecture

```
src/
├── bot/                  # Telegram bot (aiogram 3)
│   ├── routers/          # start, image, premium, referral, admin, …
│   ├── middlewares/      # DB, user, throttling, i18n
│   ├── keyboards/        # inline + reply keyboards
│   ├── states.py         # FSM states
│   └── __init__.py       # dispatcher setup
├── services/             # Business logic
│   ├── ai/               # background removal, upscaler, enhancer
│   ├── user/             # user + subscription services
│   ├── payment/          # 5 provider integrations
│   ├── analytics/        # event tracking + referral
│   ├── admin/            # stats, broadcast, promo, plans
│   ├── notification/     # scheduler + templates
│   └── image/            # PIL processor + converter
├── database/             # SQLAlchemy models + session
├── config/               # Settings + logging
├── api/                  # FastAPI webhooks + admin API
├── utils/                # Helpers, exceptions
└── main.py               # Entrypoint
```

### Data flow

```
User → Telegram → aiogram dispatcher
                       │
                       ▼
              [middlewares]
                       │
              DB session + user + i18n
                       │
                       ▼
                [router handler]
                       │
              ┌────────┴────────┐
              ▼                 ▼
         [services]        [ai tools]
              │                 │
              ▼                 ▼
           Database          rembg / ESRGAN / GFPGAN
              │                 │
              └────────┬────────┘
                       ▼
                  Output file
```

---

## 💳 Payments

| Provider  | Country      | Currency |
|-----------|--------------|----------|
| Click     | Uzbekistan   | UZS      |
| Payme     | Uzbekistan   | UZS      |
| Stripe    | International | USD     |
| Telegram Stars | Global | XTR     |
| Crypto (NOWPayments) | Global | USDT/BTC |

---

## 📊 Admin Commands

```
/admin    — open dashboard
/stats    — quick stats
/broadcast — send to all users
/promo    — create promo code
```

---

## 🧪 Testing

```bash
pytest -q --asyncio-mode=auto
```

---

## 🛡 Production

```bash
# Build
docker build -t magic-bg-remover:latest .

# Deploy
docker-compose up -d

# Migrate
docker exec magicbg_bot alembic upgrade head

# Logs
docker logs -f magicbg_bot
```

---

## 📜 License

MIT © 2026 KRYZENSYS