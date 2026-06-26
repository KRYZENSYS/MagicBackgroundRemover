"""FastAPI app with bot + webhooks + admin API (Render-friendly)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import admin, public, webhooks
from src.bot import setup_bot
from src.config.logging import setup_logging
from src.config.settings import settings
from src.database.session import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting MagicBackgroundRemover...")
    await init_db()
    bot, dp = await setup_bot()
    app.state.bot = bot
    app.state.dp = dp
    # Register webhook router with shared bot + dp
    from src.api.routers.telegram import setup_webhook
    tg_router = setup_webhook(bot, dp, settings.SECRET_KEY)
    app.include_router(tg_router)
    # Try setting webhook automatically (best effort)
    if settings.WEBHOOK_URL or settings.WEBHOOK_BASE:
        try:
            url = settings.WEBHOOK_URL or f"{settings.WEBHOOK_BASE.rstrip('/')}{settings.WEBHOOK_PATH}"
            await bot.set_webhook(url=url, secret_token=settings.SECRET_KEY or None, drop_pending_updates=True)
            logger.info("Webhook set to %s", url)
        except Exception as e:
            logger.warning("set_webhook failed (manual /tg/set-webhook available): %s", e)
    # Start notification scheduler
    try:
        from src.services.notification.scheduler import init_scheduler
        scheduler = init_scheduler(bot)
        await scheduler.start()
        app.state.scheduler = scheduler
    except Exception as e:
        logger.warning("scheduler start failed: %s", e)
    yield
    # Shutdown
    try:
        if hasattr(app.state, "scheduler"):
            await app.state.scheduler.stop()
        for admin_id in settings.ADMIN_IDS:
            try:
                await bot.send_message(admin_id, "🔴 Bot to'xtadi.")
            except Exception:
                pass
    except Exception:
        pass
    try:
        await bot.session.close()
    except Exception:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="MagicBackgroundRemover API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(public.router, prefix="/api")
    app.include_router(webhooks.router, prefix="/webhook")
    app.include_router(admin.router, prefix="/api/admin")

    @app.get("/health")
    async def health():
        return JSONResponse({"status": "ok"})

    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    return app


app = create_app()


__all__ = ["create_app", "app"]