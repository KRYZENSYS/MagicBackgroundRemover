"""Project-wide enums and constants."""
from __future__ import annotations

from enum import Enum, IntEnum


class PlanTier(IntEnum):
    FREE = 0
    TRIAL = 1
    PREMIUM = 2
    VIP = 3

    @property
    def display(self) -> str:
        return self.name.title()


class SubscriptionPlan(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"
    TRIAL = "trial"


class PaymentProvider(str, Enum):
    TELEGRAM_STARS = "stars"
    CLICK = "click"
    PAYME = "payme"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    MANUAL = "manual"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class ImageTool(str, Enum):
    BG_REMOVE = "bg_remove"
    BG_REPLACE = "bg_replace"
    BG_COLOR = "bg_color"
    BG_GRADIENT = "bg_gradient"
    UPSCALE_2X = "upscale_2x"
    UPSCALE_4X = "upscale_4x"
    UPSCALE_8X = "upscale_8x"
    ENHANCE = "enhance"
    FACE_ENHANCE = "face_enhance"
    DENOISE = "denoise"
    SHARPEN = "sharpen"
    PORTRAIT = "portrait"
    BLUR_BG = "blur_bg"
    PASSPORT = "passport"
    ID_PHOTO = "id_photo"
    PRODUCT = "product"
    RESIZE = "resize"
    COMPRESS = "compress"
    CONVERT = "convert"
    ROTATE = "rotate"
    FLIP = "flip"
    WATERMARK_ADD = "watermark_add"
    WATERMARK_REMOVE = "watermark_remove"
    CROP = "crop"


class AIModel(str, Enum):
    U2NET = "u2net"
    U2NETP = "u2netp"
    U2NET_HUMAN = "u2net_human_seg"
    U2NET_CLOTH = "u2net_cloth_seg"
    SILUETA = "silueta"
    ISNET = "isnet-general-use"


class BackgroundColor(str, Enum):
    TRANSPARENT = "transparent"
    WHITE = "#FFFFFF"
    BLACK = "#000000"
    RED = "#FF0000"
    BLUE = "#0000FF"
    GREEN = "#00FF00"
    YELLOW = "#FFFF00"
    CUSTOM = "custom"


class UserStatus(str, Enum):
    ACTIVE = "active"
    BANNED = "banned"
    WARNED = "warned"
    SUSPENDED = "suspended"


class Locale(str, Enum):
    UZ = "uz"
    RU = "ru"
    EN = "en"


class LogEvent(str, Enum):
    USER_REGISTER = "user_register"
    USER_BAN = "user_ban"
    USER_UNBAN = "user_unban"
    USER_WARN = "user_warn"
    IMAGE_PROCESS = "image_process"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_ACTIVE = "subscription_active"
    ADMIN_BROADCAST = "admin_broadcast"
    ADMIN_ACTION = "admin_action"
    API_CALL = "api_call"
    ERROR = "error"
    SECURITY_ALERT = "security_alert"


# Passport / ID photo sizes (width x height in pixels at 300 DPI)
PASSPORT_SIZES = {
    "uz_35x45": (413, 531),
    "ru_30x40": (354, 472),
    "us_2x2": (600, 600),
    "eu_35x45": (413, 531),
    "schengen": (413, 531),
}


# File extensions
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
ALLOWED_DOC_EXT = {".pdf"}

# Cache keys
CACHE_KEY_USER = "user:{telegram_id}"
CACHE_KEY_STATS = "stats:global"
CACHE_KEY_RATE = "rate:{user_id}:{action}"

# Limits
MAX_IMAGE_DIMENSION = 4096
MAX_BATCH_FILES = 10
RATE_LIMIT_PER_MINUTE = 30
RATE_LIMIT_PER_HOUR = 200
CAPTCHA_TTL = 300


__all__ = [
    "PlanTier",
    "SubscriptionPlan",
    "PaymentProvider",
    "PaymentStatus",
    "ImageTool",
    "AIModel",
    "BackgroundColor",
    "UserStatus",
    "Locale",
    "LogEvent",
    "PASSPORT_SIZES",
    "ALLOWED_IMAGE_EXT",
    "ALLOWED_DOC_EXT",
    "MAX_IMAGE_DIMENSION",
    "MAX_BATCH_FILES",
    "RATE_LIMIT_PER_MINUTE",
    "RATE_LIMIT_PER_HOUR",
    "CAPTCHA_TTL",
]