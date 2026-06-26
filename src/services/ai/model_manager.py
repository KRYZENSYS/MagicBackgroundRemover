"""Singleton AI model loader with lazy init, GPU detection, and warm-up."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from src.config.logging import logger
from src.config.settings import settings

try:
    import torch
    HAS_TORCH = True
except Exception:  # pragma: no cover
    HAS_TORCH = False


class ModelManager:
    def __init__(self):
        self.device = self._detect_device()
        self._cache: dict[str, Any] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._loaded: set[str] = set()
        self._models_dir = Path(settings.MODELS_DIR)
        self._models_dir.mkdir(parents=True, exist_ok=True)

    def _detect_device(self) -> str:
        if not HAS_TORCH:
            return "cpu"
        if settings.FORCE_CPU:
            return "cpu"
        try:
            return "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        except Exception:
            return "cpu"

    def has_cuda(self) -> bool:
        return self.device == "cuda"

    async def get(self, name: str, loader):
        """Async-safe lazy loader. `loader` is a callable returning the model."""
        if name in self._loaded:
            return self._cache[name]
        lock = self._locks.setdefault(name, asyncio.Lock())
        async with lock:
            if name in self._loaded:
                return self._cache[name]
            logger.info("Loading AI model: %s (device=%s)", name, self.device)
            try:
                model = await asyncio.to_thread(loader)
            except Exception as e:
                logger.exception("Failed to load model %s: %s", name, e)
                raise
            self._cache[name] = model
            self._loaded.add(name)
            return model

    def unload(self, name: str):
        if name in self._cache:
            del self._cache[name]
            self._loaded.discard(name)
            logger.info("Unloaded model %s", name)

    def status(self) -> dict:
        return {
            "device": self.device,
            "loaded": list(self._loaded),
            "models_dir": str(self._models_dir),
        }


model_manager = ModelManager()
__all__ = ["ModelManager", "model_manager"]