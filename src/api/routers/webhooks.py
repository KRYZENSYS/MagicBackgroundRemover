"""Webhook router for payment providers."""
from __future__ import annotations

from fastapi import APIRouter, Request

from src.config.logging import logger
from src.database.session import async_session
from src.services.payment.provider import PaymentManager

router = APIRouter(tags=["webhooks"])


@router.post("/click")
async def click_webhook(request: Request):
    body = await request.json()
    logger.info("Click webhook: %s", body)
    async with async_session() as session:
        mgr = PaymentManager(session)
        result = await mgr.get("click").handle_webhook(body)
        if result.get("status") == "completed" and "order_id" in body:
            from sqlalchemy import select
            from src.database.models.payment import Payment
            order_id = body.get("order_id") or body.get("merchant_trans_id")
            payment = await session.execute(
                select(Payment).where(Payment.provider_payment_id == str(order_id))
            )
            p = payment.scalar_one_or_none()
            if p:
                await mgr.confirm(p.id, success=True)
    return {"ok": True}


@router.post("/payme")
async def payme_webhook(request: Request):
    body = await request.json()
    logger.info("Payme webhook: %s", body)
    async with async_session() as session:
        mgr = PaymentManager(session)
        result = await mgr.get("payme").handle_webhook(body)
        if result.get("status") == "completed":
            params = body.get("params", {})
            order_id = params.get("account", {}).get("order_id")
            if order_id:
                from sqlalchemy import select
                from src.database.models.payment import Payment
                payment = await session.execute(
                    select(Payment).where(Payment.provider_payment_id == order_id)
                )
                p = payment.scalar_one_or_none()
                if p:
                    await mgr.confirm(p.id, success=True)
    return {"ok": True}


@router.post("/stripe")
async def stripe_webhook(request: Request):
    body = await request.json()
    logger.info("Stripe webhook: %s", body.get("type"))
    async with async_session() as session:
        mgr = PaymentManager(session)
        result = await mgr.get("stripe").handle_webhook(body)
        if result.get("status") == "completed":
            session_id = result.get("session")
            if session_id:
                from sqlalchemy import select
                from src.database.models.payment import Payment
                payment = await session.execute(
                    select(Payment).where(Payment.payload["session_id"].astext == session_id)
                )
                p = payment.scalar_one_or_none()
                if p:
                    await mgr.confirm(p.id, success=True)
    return {"ok": True}


@router.post("/crypto")
async def crypto_webhook(request: Request):
    body = await request.json()
    logger.info("Crypto webhook: %s", body)
    async with async_session() as session:
        mgr = PaymentManager(session)
        result = await mgr.get("crypto").handle_webhook(body)
        if result.get("status") == "completed":
            order_id = body.get("order_id")
            if order_id:
                from sqlalchemy import select
                from src.database.models.payment import Payment
                payment = await session.execute(
                    select(Payment).where(Payment.provider_payment_id == order_id)
                )
                p = payment.scalar_one_or_none()
                if p:
                    await mgr.confirm(p.id, success=True)
    return {"ok": True}


__all__ = ["router"]