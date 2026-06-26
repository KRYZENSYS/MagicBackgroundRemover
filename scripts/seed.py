"""Seed initial plans into the database."""
from __future__ import annotations

import asyncio

from src.database.session import async_session, init_db
from src.services.user.subscription import SubscriptionService

PLANS = [
    {"code": "monthly",   "name": "Premium Oylik",  "price": 19900,  "currency": "UZS", "duration_days": 30},
    {"code": "quarterly", "name": "Premium 3 Oylik", "price": 49900,  "currency": "UZS", "duration_days": 90},
    {"code": "yearly",    "name": "Premium Yillik", "price": 179900, "currency": "UZS", "duration_days": 365},
    {"code": "lifetime",  "name": "Premium Lifetime", "price": 999900, "currency": "UZS", "duration_days": 36500},
]


async def main():
    await init_db()
    async with async_session() as session:
        svc = SubscriptionService(session)
        for p in PLANS:
            existing = await svc.get_plan(p["code"])
            if existing:
                continue
            await svc.create_plan(**p)
            print(f"+ created plan {p['code']}")
        print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())