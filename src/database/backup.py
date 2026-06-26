"""Database backup / restore helpers."""
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from src.config.logging import logger
from src.config.settings import settings


async def backup_database() -> Path:
    """Create a timestamped SQLite backup file. Returns the backup path."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        raise NotImplementedError("Backup currently supports SQLite only")

    settings.DATABASE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    src = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    if src == ":memory:":
        raise ValueError("Cannot backup in-memory database")

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dst = settings.DATABASE_BACKUP_DIR / f"backup_{ts}.db"

    # Use sqlite3 backup API for safety (no file lock issues)
    src_conn = sqlite3.connect(src)
    try:
        dst_conn = sqlite3.connect(dst)
        try:
            with dst_conn:
                src_conn.backup(dst_conn)
            logger.info("Backup created: %s", dst)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()
    return dst


def restore_database(backup_path: Path) -> None:
    if not backup_path.exists():
        raise FileNotFoundError(backup_path)
    dst = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    shutil.copy2(backup_path, dst)
    logger.info("Database restored from %s", backup_path)


def list_backups() -> list[Path]:
    settings.DATABASE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(settings.DATABASE_BACKUP_DIR.glob("backup_*.db"), reverse=True)


def prune_backups(keep: int = 30) -> None:
    backups = list_backups()
    for old in backups[keep:]:
        try:
            old.unlink()
        except OSError as e:
            logger.warning("Could not remove old backup %s: %s", old, e)


__all__ = ["backup_database", "restore_database", "list_backups", "prune_backups"]