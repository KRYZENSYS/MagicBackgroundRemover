"""Background removal service using rembg."""
from __future__ import annotations

import io
import logging
from typing import Optional

from PIL import Image
from rembg import remove

from src.config.settings import settings

logger = logging.getLogger(__name__)


class BackgroundRemover:
    """Wraps rembg with caching and post-processing."""

    def __init__(self):
        self._cache: dict[int, bytes] = {}
        self._model_name = settings.BG_REMOVAL_MODEL

    async def remove_background(self, img_bytes: bytes) -> bytes:
        """Remove background from image bytes."""
        try:
            result = remove(img_bytes, session=None)
            return result
        except Exception as e:
            logger.exception("bg_removal failed: %s", e)
            raise

    async def solid_color_background(self, img_bytes: bytes, color: str = "#FFFFFF") -> bytes:
        """Replace background with a solid color."""
        no_bg = await self.remove_background(img_bytes)
        fg = Image.open(io.BytesIO(no_bg)).convert("RGBA")
        bg = Image.new("RGBA", fg.size, color)
        bg.paste(fg, mask=fg.split()[3])
        out = io.BytesIO()
        bg.convert("RGB").save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def gradient_background(
        self,
        img_bytes: bytes,
        color_a: str = "#FFFFFF",
        color_b: str = "#000000",
        direction: str = "vertical",
    ) -> bytes:
        """Replace background with a gradient."""
        no_bg = await self.remove_background(img_bytes)
        fg = Image.open(io.BytesIO(no_bg)).convert("RGBA")
        w, h = fg.size
        grad = Image.new("RGB", (w, h), color_a)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(grad)
        steps = max(w, h)
        for i in range(steps):
            ratio = i / steps
            r = int(int(color_a[1:3], 16) * (1 - ratio) + int(color_b[1:3], 16) * ratio)
            g = int(int(color_a[3:5], 16) * (1 - ratio) + int(color_b[3:5], 16) * ratio)
            b = int(int(color_a[5:7], 16) * (1 - ratio) + int(color_b[5:7], 16) * ratio)
            if direction == "vertical":
                draw.line([(0, i), (w, i)], fill=(r, g, b))
            else:
                draw.line([(i, 0), (i, h)], fill=(r, g, b))
        grad = grad.convert("RGBA")
        grad.paste(fg, mask=fg.split()[3])
        out = io.BytesIO()
        grad.convert("RGB").save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def image_background(self, img_bytes: bytes, bg_bytes: bytes) -> bytes:
        """Replace background with another image."""
        no_bg = await self.remove_background(img_bytes)
        fg = Image.open(io.BytesIO(no_bg)).convert("RGBA")
        bg = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
        bg = bg.resize(fg.size)
        bg.paste(fg, mask=fg.split()[3])
        out = io.BytesIO()
        bg.convert("RGB").save(out, format="PNG", optimize=True)
        return out.getvalue()


bg_remover = BackgroundRemover()

__all__ = ["BackgroundRemover", "bg_remover"]