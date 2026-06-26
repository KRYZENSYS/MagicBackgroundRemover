"""Image storage abstraction (local + S3-compatible)."""
from __future__ import annotations

import asyncio
import io
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import aiofiles

from src.config.settings import settings

logger = logging.getLogger(__name__)


class ImageStorage:
    """Saves processed images locally with auto-cleanup."""

    def __init__(self):
        self.base_path = Path(settings.STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=settings.STORAGE_TTL_HOURS)

    async def save(self, img_bytes: bytes, ext: str = "png", user_id: int | None = None) -> str:
        prefix = f"{user_id}_" if user_id else ""
        filename = f"{prefix}{uuid.uuid4().hex}.{ext.lstrip('.')}"
        path = self.base_path / filename
        async with aiofiles.open(path, "wb") as f:
            await f.write(img_bytes)
        return filename

    async def load(self, filename: str) -> bytes:
        path = self.base_path / filename
        if not path.exists():
            raise FileNotFoundError(filename)
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete(self, filename: str) -> bool:
        path = self.base_path / filename
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False

    async def cleanup_expired(self) -> int:
        """Remove files older than TTL. Returns count deleted."""
        now = datetime.utcnow()
        removed = 0
        for path in self.base_path.iterdir():
            try:
                mtime = datetime.utcfromtimestamp(path.stat().st_mtime)
                if now - mtime > self.ttl:
                    path.unlink()
                    removed += 1
            except Exception as e:
                logger.warning("cleanup %s: %s", path, e)
        return removed


image_storage = ImageStorage()

__all__ = ["ImageStorage", "image_storage"]