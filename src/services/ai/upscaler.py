"""Image upscaling service."""
from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


class Upscaler:
    """Upscale images using PIL LANCZOS resampling."""

    async def upscale(self, img_bytes: bytes, factor: int = 2) -> bytes:
        if factor not in (2, 4):
            raise ValueError("factor must be 2 or 4")
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        w, h = img.size
        new_size = (w * factor, h * factor)
        result = img.resize(new_size, Image.LANCZOS)
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()


upscaler = Upscaler()

__all__ = ["Upscaler", "upscaler"]