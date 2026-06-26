# MagicBackground Remover — Enterprise SAAS Platform

Professional Telegram AI platform for background removal, image enhancement, and editing — built with 100+ features, modular architecture, and production-grade infrastructure.

## Xususiyatlar (100+)

### AI Capabilities
- Background removal (HD / Ultra HD)
- AI upscale (2x / 4x / 8x)
- AI enhance, denoise, sharpen
- AI face / skin / hair / edge refinement
- AI shadow & reflection
- AI portrait mode & background blur
- Replace background (gradient / solid / image)
- Passport / ID / product / e-commerce modes
- Auto crop, center, color correction

### Image Tools
- Resize, compress, rotate, flip
- PNG/JPG/WebP conversion
- Watermark add/remove
- Batch processing + ZIP download
- Metadata viewer
- File size optimizer

### User & Premium
- Profile, history, presets, favorites
- Daily limits, plans (Monthly/Yearly/Lifetime)
- Trial, payments (Telegram Stars, Click, Payme, Stripe, Crypto)
- Referral + promo codes

### Admin
- Dashboard, stats, broadcast, scheduled
- Ban/unban/warn, logs, backups, export
- Revenue & referral analytics

### Security & Performance
- Anti-spam/flood, rate-limit, CAPTCHA
- Async, Redis cache, background queue
- Health checks, error monitoring
- Docker / Railway / Render / VPS deploy

## Tez start

```bash
git clone https://github.com/KRYZENSYS/MagicBackgroundRemover.git
cd MagicBackgroundRemover
pip install -r requirements.txt
cp .env.example .env  # BOT_TOKEN kiriting
python -m bot
```

## Struktura

```
bot/                  # Telegram bot entry
api/                  # REST API (FastAPI)
core/                 # Config, security, middleware
services/             # AI, payment, image, storage
handlers/             # Telegram handlers
database/             # SQLite + ORM
keyboards/            # Inline/reply keyboards
localization/         # i18n (UZ/RU/EN)
utils/                # Helpers, validators
tests/                # Pytest
deployment/           # Docker, CI/CD
docs/                 # Documentation
```

## Documentation
- `docs/INSTALL.md` — O'rnatish
- `docs/DEPLOY.md` — Deploy
- `docs/API.md` — REST API
- `docs/ADMIN.md` — Admin panel
- `docs/USER.md` — User guide
- `CHANGELOG.md` — Versiyalar

## License
MIT © 2026 KRYZENSYS