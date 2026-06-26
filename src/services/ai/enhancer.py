"""Image enhancement: denoise, sharpen, brighten, enhance."""
from __future__ import annotations

import io
import logging

from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


class ImageEnhancer:
    async def denoise(self, img_bytes: bytes) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        result = img.filter(Image.Filter.SMOOTH)
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def sharpen(self, img_bytes: bytes) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        result = img.filter(Image.Filter.SHARPEN)
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def brighten(self, img_bytes: bytes, factor: float = 1.3) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        result = ImageEnhance.Brightness(img).enhance(factor)
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def enhance(self, img_bytes: bytes) -> bytes:
        """Combined enhancement: contrast + sharpness + color."""
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = ImageEnhance.Contrast(img).enhance(1.15)
        img = ImageEnhance.Color(img).enhance(1.1)
        img = ImageEnhance.Sharpness(img).enhance(1.2)
        out = io.BytesIO()
        img.save(out, format="PNG", optimize=True)
        return out.getvalue()


image_enhancer = ImageEnhancer()

__all__ = ["ImageEnhancer", "image_enhancer"]