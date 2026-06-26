"""Security utilities: rate limiting, validation, hashing."""
import hashlib
import hmac
import secrets
import time
from collections import defaultdict
from typing import Dict, Tuple
from cryptography.fernet import Fernet

from core.settings import settings


# ============= RATE LIMITER =============
class RateLimiter:
    """In-memory token bucket rate limiter."""

    def __init__(self, rate: int = 10, per: int = 60):
        self.rate = rate
        self.per = per
        self.allowance: Dict[int, Tuple[float, float]] = defaultdict(lambda: (rate, time.time()))

    def is_allowed(self, user_id: int) -> bool:
        current = time.time()
        tokens, last_update = self.allowance[user_id]
        elapsed = current - last_update
        tokens = min(self.rate, tokens + elapsed * (self.rate / self.per))
        if tokens < 1:
            self.allowance[user_id] = (tokens, current)
            return False
        tokens -= 1
        self.allowance[user_id] = (tokens, current)
        return True


# ============= ANTI-FLOOD =============
class AntiFlood:
    """Track rapid consecutive messages."""

    def __init__(self, max_messages: int = 5, window_seconds: int = 10):
        self.max = max_messages
        self.window = window_seconds
        self.history: Dict[int, list] = defaultdict(list)

    def is_flood(self, user_id: int) -> bool:
        now = time.time()
        self.history[user_id] = [t for t in self.history[user_id] if now - t < self.window]
        self.history[user_id].append(now)
        return len(self.history[user_id]) > self.max


# ============= CAPTCHA =============
class CaptchaGenerator:
    @staticmethod
    def generate() -> Tuple[str, str]:
        """Generate simple math captcha: returns (question, answer)."""
        import random
        a, b = random.randint(1, 9), random.randint(1, 9)
        op = random.choice(["+", "-", "*"])
        expr = f"{a} {op} {b}"
        answer = str(eval(expr))
        return expr, answer


# ============= ENCRYPTION =============
def _get_fernet() -> Fernet:
    key = hashlib.sha256(settings.API_SECRET_KEY.encode()).digest()
    return Fernet(__import__("base64").urlsafe_b64encode(key))


def encrypt_data(data: str) -> str:
    return _get_fernet().encrypt(data.encode()).decode()


def decrypt_data(token: str) -> str:
    return _get_fernet().decrypt(token.encode()).decode()


# ============= TOKEN GENERATION =============
def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_promo_code(length: int = 10) -> str:
    """Alphanumeric promo code."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ============= FILE VALIDATION =============
def validate_image_signature(data: bytes) -> bool:
    """Magic-byte validation."""
    if len(data) < 8:
        return False
    signatures = {
        b"\x89PNG\r\n\x1a\n": "png",
        b"\xff\xd8\xff": "jpeg",
        b"RIFF": "webp",
        b"GIF87a": "gif",
        b"GIF89a": "gif",
        b"BM": "bmp",
    }
    for sig in signatures:
        if data.startswith(sig):
            return True
    return False


# ============= HASHING =============
def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(password.encode(), hashed.encode())


# Global instances
rate_limiter = RateLimiter(rate=20, per=60)
anti_flood = AntiFlood(max_messages=8, window_seconds=5)