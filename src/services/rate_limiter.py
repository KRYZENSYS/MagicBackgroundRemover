"""Rate limiting service."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from src.config.settings import settings
from src.constants import RATE_LIMIT_PER_HOUR, RATE_LIMIT_PER_MINUTE
from src.services.cache import cache


@dataclass
class RateLimitResult:
    allowed: bool
    remaining_minute: int
    remaining_hour: int
    retry_after: int = 0


class RateLimiter:
    """Token-bucket-ish sliding window rate limiter backed by cache."""

    async def check(self, user_id: int, action: str = "default") -> RateLimitResult:
        now = int(time.time())
        minute_key = f"rate:{user_id}:{action}:min:{now // 60}"
        hour_key = f"rate:{user_id}:{action}:hour:{now // 3600}"

        minute_count = await cache.incr(minute_key, amount=1, ttl=60)
        hour_count = await cache.incr(hour_key, amount=1, ttl=3600)

        if minute_count > RATE_LIMIT_PER_MINUTE or hour_count > RATE_LIMIT_PER_HOUR:
            retry_after = 60 - (now % 60) if minute_count > RATE_LIMIT_PER_MINUTE else 3600 - (now % 3600)
            return RateLimitResult(False, 0, 0, retry_after)

        return RateLimitResult(
            allowed=True,
            remaining_minute=max(0, RATE_LIMIT_PER_MINUTE - minute_count),
            remaining_hour=max(0, RATE_LIMIT_PER_HOUR - hour_count),
        )

    async def reset(self, user_id: int, action: str = "default") -> None:
        now = int(time.time())
        await cache.delete(f"rate:{user_id}:{action}:min:{now // 60}")
        await cache.delete(f"rate:{user_id}:{action}:hour:{now // 3600}")


rate_limiter = RateLimiter()


__all__ = ["RateLimiter", "rate_limiter", "RateLimitResult"]