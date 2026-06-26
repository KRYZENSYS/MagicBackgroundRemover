"""Telegram webhook router (mounted inside FastAPI)."""
from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot
from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request

from src.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def setup_webhook(bot: Bot, dp, secret: str):
    """Register webhook handler and configure bot URL on startup."""

    @router.post(f"/tg/webhook")
    async def tg_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ):
        if secret and x_telegram_bot_api_secret_token != secret:
            raise HTTPException(status_code=403, detail="invalid_secret_token")
        data: dict[str, Any] = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return {"ok": True}

    @router.post("/tg/set-webhook")
    async def set_webhook(_: Request):
        url = settings.WEBHOOK_URL or f"{settings.WEBHOOK_BASE.rstrip('/')}{settings.WEBHOOK_PATH}"
        try:
            await bot.set_webhook(url=url, secret_token=secret or None, drop_pending_updates=True)
            return {"ok": True, "url": url}
        except Exception as e:
            logger.exception("set_webhook failed: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/tg/delete-webhook")
    async def delete_webhook():
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            return {"ok": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/tg/info")
    async def webhook_info():
        info = await bot.get_webhook_info()
        return {
            "url": info.url,
            "pending_update_count": info.pending_update_count,
            "last_error_message": info.last_error_message,
        }

    return router