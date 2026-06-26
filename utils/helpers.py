"""Helper utilities."""
from typing import List
from core.settings import settings


def format_bytes(size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def format_duration(ms: int) -> str:
    """Format milliseconds to readable string."""
    if ms < 1000:
        return f"{ms}ms"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    return f"{minutes:.1f}m"


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate text with ellipsis."""
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def parse_command_args(text: str) -> List[str]:
    """Parse command arguments."""
    parts = text.split(maxsplit=1)
    return parts[1].split() if len(parts) > 1 else []


def build_referral_link(telegram_id: int) -> str:
    """Build referral deep-link."""
    return f"https://t.me/{settings.BOT_USERNAME}?start=ref_{telegram_id}"


def mask_card_number(number: str) -> str:
    """Mask sensitive payment data."""
    if len(number) < 8:
        return "*" * len(number)
    return number[:4] + "*" * (len(number) - 8) + number[-4:]