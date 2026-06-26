"""File storage with optional S3-compatible backend."""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, BinaryIO

from core.settings import settings
from core.logger import logger


class StorageService:
    """Local + S3 storage abstraction."""

    def __init__(self):
        self.base = Path(settings.STORAGE_PATH)
        self.base.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    async def save_bytes(self, data: bytes, folder: str = "uploads", extension: str = "png") -> str:
        """Save bytes and return relative path."""
        if len(data) > self.max_size_bytes:
            raise ValueError(f"File too large: {len(data)} bytes")
        key = f"{folder}/{uuid.uuid4().hex}.{extension.lstrip('.')}"
        full = self.base / key
        full.parent.mkdir(parents=True, exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)
        return key

    async def load_bytes(self, key: str) -> bytes:
        full = self.base / key
        if not full.exists():
            raise FileNotFoundError(key)
        return full.read_bytes()

    async def delete(self, key: str) -> None:
        full = self.base / key
        if full.exists():
            full.unlink()

    async def cleanup_old(self, days: int = 7) -> int:
        """Delete files older than N days."""
        import time
        count = 0
        threshold = time.time() - days * 86400
        for path in self.base.rglob("*"):
            if path.is_file() and path.stat().st_mtime < threshold:
                path.unlink()
                count += 1
        logger.info(f"Cleaned {count} old files")
        return count

    async def get_disk_usage(self) -> dict:
        total = 0
        files = 0
        for path in self.base.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
                files += 1
        return {"files": files, "bytes": total, "mb": round(total / (1024 * 1024), 2)}


storage = StorageService()