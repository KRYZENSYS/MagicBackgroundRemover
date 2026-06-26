"""Image validation: format, size, dimensions."""
from __future__ import annotations

import io
import logging

from PIL import Image

from src.config.settings import settings

logger = logging.getLogger(__name__)


class ImageValidator:
    def inspect(self, img_bytes: bytes) -> dict:
        if not img_bytes:
            raise ValueError("Bo'sh rasm")
        if len(img_bytes) > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"Rasm {settings.MAX_IMAGE_SIZE_MB}MB dan katta")
        try:
            img = Image.open(io.BytesIO(img_bytes))
            img.verify()
        except Exception as e:
            raise ValueError(f"Rasm buzilgan: {e}")
        img = Image.open(io.BytesIO(img_bytes))
        w, h = img.size
        if w < settings.MIN_IMAGE_DIMENSION or h < settings.MIN_IMAGE_DIMENSION:
            raise ValueError(f"Rasm juda kichik (min {settings.MIN_IMAGE_DIMENSION}px)")
        if w > settings.MAX_IMAGE_DIMENSION or h > settings.MAX_IMAGE_DIMENSION:
            raise ValueError(f"Rasm juda katta (max {settings.MAX_IMAGE_DIMENSION}px)")
        return {
            "width": w,
            "height": h,
            "format": img.format,
            "mode": img.mode,
            "size_bytes": len(img_bytes),
        }


image_validator = ImageValidator()

__all__ = ["ImageValidator", "image_validator"]