"""File storage service - abstracts local FS vs S3."""
from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

import aiofiles

from src.config.logging import logger
from src.config.settings import settings


class StorageService:
    """Async file storage with content-addressable filenames."""

    def __init__(self) -> None:
        self.base = settings.STORAGE_DIR
        self.temp = settings.TEMP_DIR
        self.cache = settings.CACHE_DIR
        for p in (self.base, self.temp, self.cache):
            p.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()[:16]

    async def save_bytes(self, data: bytes, subdir: str = "uploads", ext: str = ".png") -> Path:
        h = self.hash_bytes(data) + "_" + uuid.uuid4().hex[:8]
        folder = self.base / subdir
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{h}{ext}"
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)
        return path

    async def save_upload(self, upload: BinaryIO, subdir: str = "uploads", ext: str = ".bin") -> Path:
        data = upload.read()
        return await self.save_bytes(data, subdir, ext)

    async def read(self, path: Path) -> bytes:
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete(self, path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError as e:
            logger.warning("Could not delete %s: %s", path, e)

    def temp_path(self, ext: str = ".png") -> Path:
        name = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}{ext}"
        return self.temp / name

    async def write_temp(self, data: bytes, ext: str = ".png") -> Path:
        path = self.temp_path(ext)
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)
        return path

    async def cleanup_temp(self, max_age_seconds: int = 3600) -> int:
        """Remove temp files older than max_age. Returns count removed."""
        removed = 0
        now = time.time()
        for path in self.temp.glob("*"):
            try:
                if path.is_file() and now - path.stat().st_mtime > max_age_seconds:
                    path.unlink()
                    removed += 1
            except OSError:
                pass
        return removed

    async def cleanup_storage(self, max_age_seconds: int = 86400 * 7) -> int:
        removed = 0
        now = time.time()
        for sub in (self.base,).iterdir() if self.base.exists() else []:
            if not sub.is_dir():
                continue
            for path in sub.glob("*"):
                try:
                    if path.is_file() and now - path.stat().st_mtime > max_age_seconds:
                        path.unlink()
                        removed += 1
                except OSError:
                    pass
        return removed

    def total_size(self) -> int:
        return sum(p.stat().st_size for p in self.base.rglob("*") if p.is_file())

    def disk_usage(self) -> dict:
        usage = shutil.disk_usage(self.base)
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": round(usage.used / usage.total * 100, 1) if usage.total else 0,
        }


storage = StorageService()

__all__ = ["StorageService", "storage"]