"""Face enhancement service."""
from __future__ import annotations

import io
import logging

from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


class FaceEnhancer:
    async def enhance_face(self, img_bytes: bytes) -> bytes:
        """Enhance face: smooth skin + sharpen eyes + brighten."""
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        # Smooth (skin)
        smooth = img.filter(Image.Filter.SMOOTH)
        # Sharpen (eyes/details)
        sharp = img.filter(Image.Filter.SHARPEN)
        # Blend
        result = Image.blend(smooth, sharp, 0.5)
        # Brighten slightly
        result = ImageEnhance.Brightness(result).enhance(1.05)
        result = ImageEnhance.Contrast(result).enhance(1.05)
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()


face_enhancer = FaceEnhancer()

__all__ = ["FaceEnhancer", "face_enhancer"]