"""Helper utilities for bot handlers."""
from __future__ import annotations

from typing import Any

from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def truncate(s: str, n: int = 100) -> str:
    return s if len(s) <= n else s[: n - 1] + "\u2026"


async def safe_edit(target: Message | CallbackQuery, text: str, **kwargs) -> bool:
    """Safely edit a message text. Returns True on success."""
    try:
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text, **kwargs)
        else:
            await target.edit_text(text, **kwargs)
        return True
    except TelegramAPIError as e:
        if "message is not modified" in str(e):
            return True
        return False


async def safe_answer(call: CallbackQuery, text: str = "", show_alert: bool = False) -> None:
    try:
        await call.answer(text, show_alert=show_alert)
    except TelegramAPIError:
        pass


__all__ = ["format_bytes", "format_duration", "truncate", "safe_edit", "safe_answer"]