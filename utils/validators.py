"""Validators."""
import re
from typing import Optional


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def is_valid_phone(phone: str) -> bool:
    return bool(re.match(r"^\+?[1-9]\d{7,14}$", phone))


def is_valid_promo_code(code: str) -> bool:
    return bool(re.match(r"^[A-Z0-9]{4,20}$", code.upper()))


def is_valid_image_extension(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in {"jpg", "jpeg", "png", "webp"}


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Strip potentially dangerous characters."""
    text = re.sub(r"<[^>]+>", "", text)
    return text[:max_length]


def parse_int_safe(value: str, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default