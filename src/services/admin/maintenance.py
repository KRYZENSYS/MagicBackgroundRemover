"""Maintenance toggle (in-memory)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MaintenanceService:
    def __init__(self):
        self._on = False

    def is_on(self) -> bool:
        return self._on

    def set(self, on: bool) -> None:
        self._on = on
        logger.warning("Maintenance mode: %s", "ON" if on else "OFF")


maintenance_service = MaintenanceService()

__all__ = ["MaintenanceService", "maintenance_service"]