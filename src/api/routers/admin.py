"""Admin API endpoints (protected by token)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header

from src.config.settings import settings
from src.database.session import async_session
from src.services.admin.admin import AdminService
from src.services.admin.broadcast import BroadcastService
from src.services.admin.promo import PromoAdminService
from src.services.admin.plan_admin import PlanAdminService

router = APIRouter(tags=["admin"])


def _check_admin(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="invalid_token")
    return True


@router.get("/stats")
async def get_stats(_: bool = Depends(_check_admin)):
    async with async_session() as session:
        svc = AdminService(session)
        return await svc.deep_stats()


@router.get("/users/search")
async def search_users(q: str, limit: int = 10, _: bool = Depends(_check_admin)):
    async with async_session() as session:
        svc = AdminService(session)
        users = await svc.search_users(q, limit=limit)
        return [
            {
                "id": u.id,
                "username": u.username,
                "first_name": u.first_name,
                "is_premium": u.is_premium,
                "premium_until": u.premium_until.isoformat() if u.premium_until else None,
            }
            for u in users
        ]


@router.get("/payments")
async def recent_payments(limit: int = 20, _: bool = Depends(_check_admin)):
    async with async_session() as session:
        svc = AdminService(session)
        payments = await svc.recent_payments(limit)
        return [
            {
                "id": p.id,
                "user_id": p.user_id,
                "plan_code": p.plan_code,
                "provider": p.provider,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
        ]


@router.post("/broadcast")
async def broadcast(text: str, confirm: bool = False, _: bool = Depends(_check_admin)):
    async with async_session() as session:
        svc = BroadcastService(session)
        if not confirm:
            count = await svc.queue_broadcast(text)
            return {"queued": True, "target_count": count}
        sent = await svc.start_pending()
        return {"sent": sent}


@router.post("/promo")
async def create_promo(
    code: str, days: int = 0, discount: int = 0, limit: int = 100,
    _: bool = Depends(_check_admin),
):
    async with async_session() as session:
        svc = PromoAdminService(session)
        promo = await svc.create(code, days, discount, limit)
        return {"id": promo.id, "code": promo.code}


@router.post("/plan")
async def create_plan(
    code: str, name: str, price: int, currency: str, duration_days: int,
    _: bool = Depends(_check_admin),
):
    async with async_session() as session:
        svc = PlanAdminService(session)
        plan = await svc.create(code, name, price, currency, duration_days)
        return {"id": plan.id, "code": plan.code}


@router.get("/settings/{key}")
async def get_setting(key: str, _: bool = Depends(_check_admin)):
    async with async_session() as session:
        svc = AdminService(session)
        return {"key": key, "value": await svc.get_setting(key, "")}


@router.post("/settings/{key}")
async def set_setting(key: str, value: str, _: bool = Depends(_check_admin)):
    async with async_session() as session:
        svc = AdminService(session)
        await svc.set_setting(key, value)
        return {"ok": True}


__all__ = ["router"]