"""FastAPI app for webhooks + admin API."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import webhooks, admin, public

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="MagicBackgroundRemover API",
        description="Backend API for the bot: webhooks, payments, admin.",
        version="1.0.0",
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

    @app.on_event("startup")
    async def on_startup():
        logger.info("FastAPI started.")

    return app


app = create_app()


__all__ = ["create_app", "app"]