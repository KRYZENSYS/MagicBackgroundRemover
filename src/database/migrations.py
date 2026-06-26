"""Lightweight migration runner using metadata snapshots."""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import logger
from src.database.session import engine


MIGRATIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT NOT NULL
)
"""


async def ensure_migrations_table() -> None:
    async with engine.begin() as conn:
        await conn.execute(text(MIGRATIONS_TABLE_DDL))


async def applied_migrations(session: AsyncSession) -> list[str]:
    rows = await session.execute(text("SELECT name FROM schema_migrations ORDER BY id"))
    return [r[0] for r in rows.all()]


async def apply_migration(name: str, sql: str) -> None:
    """Apply a single SQL migration idempotently."""
    await ensure_migrations_table()
    checksum = hashlib.sha256(sql.encode()).hexdigest()[:16]

    async with engine.begin() as conn:
        existing = await conn.execute(
            text("SELECT checksum FROM schema_migrations WHERE name = :n"), {"n": name}
        )
        row = existing.first()
        if row:
            if row[0] != checksum:
                logger.warning("Migration %s checksum differs - skipping", name)
            return
        logger.info("Applying migration %s", name)
        await conn.execute(text(sql))
        await conn.execute(
            text("INSERT INTO schema_migrations (name, checksum, applied_at) VALUES (:n, :c, :t)"),
            {"n": name, "c": checksum, "t": datetime.utcnow()},
        )


async def run_all() -> None:
    """Apply all bundled migrations."""
    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        return
    for f in sorted(migrations_dir.glob("*.sql")):
        await apply_migration(f.stem, f.read_text(encoding="utf-8"))


__all__ = ["apply_migration", "run_all", "ensure_migrations_table"]