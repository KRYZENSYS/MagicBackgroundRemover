"""Production-grade logging with loguru + Sentry."""
import sys
from pathlib import Path
from loguru import logger as _logger
from core.settings import settings


def setup_logger():
    """Configure logger with file rotation, console output, and optional Sentry."""
    _logger.remove()

    # Console
    _logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True,
    )

    # File with rotation
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    _logger.add(
        log_path / "app.log",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
    )

    # Error file
    _logger.add(
        log_path / "errors.log",
        rotation="50 MB",
        retention="60 days",
        level="ERROR",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    # Optional Sentry
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENV, traces_sample_rate=0.2)
            _logger.info("Sentry initialized")
        except Exception as e:
            _logger.warning(f"Sentry init failed: {e}")

    return _logger


logger = setup_logger()