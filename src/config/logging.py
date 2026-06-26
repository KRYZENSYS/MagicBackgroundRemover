"""Structured logging configuration with rotation."""
from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

from src.config.settings import settings


class ColoredFormatter(logging.Formatter):
    """ANSI-coloured formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def setup_logging() -> logging.Logger:
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = settings.LOG_DIR / "bot.log"

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    for handler in list(root.handlers):
        root.removeHandler(handler)

    fmt = "%(asctime)s | %(levelname)-18s | %(name)-30s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # File with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=20 * 1024 * 1024, backupCount=10, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(fmt, datefmt))
    root.addHandler(file_handler)

    # Console
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(ColoredFormatter(fmt, datefmt))
    root.addHandler(console)

    # Quieten noisy libs
    for name in ("aiogram", "aiohttp", "asyncio"):
        logging.getLogger(name).setLevel(logging.WARNING)

    return logging.getLogger("MagicBG")


logger = setup_logging()


__all__ = ["logger", "setup_logging"]