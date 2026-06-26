"""Public API: plans, stats, info (no auth)."""
from __future__ import annotations

from fastapi import APIRouter

from src.config.settings import settings
from src.database.session import async_session
from src.services.user.subscription import SubscriptionService
from src.services.admin.admin import AdminService

router = APIRouter(tags=["public"])


@router.get("/info")
async def info():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/plans")
async def list_plans():
    async with async_session() as session:
        svc = SubscriptionService(session)
        plans = await svc.list_active()
        return [
            {
                "code": p.code,
                "name": p.name,
                "price": p.price,
                "currency": p.currency,
                "duration_days": p.duration_days,
            }
            for p in plans
        ]


@router.get("/public-stats")
async def public_stats():
    """Anonymized stats for the website landing page."""
    async with async_session() as session:
        svc = AdminService(session)
        s = await svc.quick_stats()
        return {
            "users_count": s["users"],
            "images_processed": s["today_ops"],
        }


__all__ = ["router"]