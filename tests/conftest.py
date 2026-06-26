"""Pytest config: shared fixtures."""
from __future__ import annotations

import asyncio
import os

import pytest


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
def set_test_env():
    os.environ.setdefault("BOT_TOKEN", "test-token")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("ADMIN_IDS", "1")
    yield