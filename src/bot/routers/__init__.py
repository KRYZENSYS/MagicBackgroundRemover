from .start import start_router
from .menu import menu_router
from .image import image_router
from .background import background_router
from .upscale import upscale_router
from .passport import passport_router
from .effects import effects_router
from .premium import premium_router
from .settings import settings_router
from .admin import admin_router
from .referral import referral_router
from .support import support_router
from .errors import errors_router

__all__ = [
    "start_router",
    "menu_router",
    "image_router",
    "background_router",
    "upscale_router",
    "passport_router",
    "effects_router",
    "premium_router",
    "settings_router",
    "admin_router",
    "referral_router",
    "support_router",
    "errors_router",
]