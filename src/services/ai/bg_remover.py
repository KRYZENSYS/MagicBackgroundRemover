"""Background removal service. Tries rembg first, falls back to classical CV."""
from __future__ import annotations

import io

from PIL import Image

from src.config.logging import logger


class BgRemover:
    def __init__(self):
        self._model = None
        self._has_rembg = False
        try:
            import rembg  # noqa: F401
            self._has_rembg = True
        except ImportError:
            logger.warning("rembg not installed; falling back to classical CV background removal.")

    async def _ensure_model(self):
        if self._model is None and self._has_rembg:
            from rembg import new_session
            from src.services.ai.model_manager import model_manager
            self._model = await model_manager.get("u2net", lambda: new_session("u2net"))
        return self._model

    async def remove_background(self, img_bytes: bytes) -> bytes:
        if self._has_rembg:
            model = await self._ensure_model()
            from rembg import remove as rembg_remove
            import asyncio
            return await asyncio.to_thread(rembg_remove, img_bytes, session=model)
        # Fallback: alpha-based simple segmentation (white background)
        return await _fallback_remove(img_bytes)

    async def solid_color_background(self, img_bytes: bytes, color: str) -> bytes:
        cut = await self.remove_background(img_bytes)
        fg = Image.open(io.BytesIO(cut)).convert("RGBA")
        bg = Image.new("RGBA", fg.size, color)
        bg.paste(fg, mask=fg.split()[3])
        out = io.BytesIO()
        bg.convert("RGB").save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def gradient_background(
        self, img_bytes: bytes, color_a: str, color_b: str, direction: str = "vertical"
    ) -> bytes:
        cut = await self.remove_background(img_bytes)
        fg = Image.open(io.BytesIO(cut)).convert("RGBA")
        w, h = fg.size
        grad = Image.new("RGB", (w, h), color_a)
        from PIL import ImageDraw
        d = ImageDraw.Draw(grad)
        steps = h if direction == "vertical" else w
        c1 = Image.new("RGB", (1, 1), color_a).getpixel((0, 0))
        c2 = Image.new("RGB", (1, 1), color_b).getpixel((0, 0))
        for i in range(steps):
            t = i / max(1, steps - 1)
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            if direction == "vertical":
                d.line([(0, i), (w, i)], fill=(r, g, b))
            else:
                d.line([(i, 0), (i, h)], fill=(r, g, b))
        grad = grad.convert("RGBA")
        grad.paste(fg, mask=fg.split()[3])
        out = io.BytesIO()
        grad.convert("RGB").save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def image_background(self, fg_bytes: bytes, bg_bytes: bytes) -> bytes:
        cut = await self.remove_background(fg_bytes)
        fg = Image.open(io.BytesIO(cut)).convert("RGBA")
        bg = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
        bg = bg.resize(fg.size)
        bg.paste(fg, mask=fg.split()[3])
        out = io.BytesIO()
        bg.convert("RGB").save(out, format="PNG", optimize=True)
        return out.getvalue()


async def _fallback_remove(img_bytes: bytes) -> bytes:
    """Rough fallback: assumes white background and uses simple thresholding."""
    import numpy as np
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    arr = np.array(img)
    # Find pixels close to white
    diff = arr.max(axis=2) - arr.min(axis=2)
    mask = (arr.min(axis=2) > 240) & (diff < 10)
    alpha = np.where(mask, 0, 255).astype("uint8")
    rgba = np.dstack([arr, alpha])
    out = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


bg_remover = BgRemover()
__all__ = ["BgRemover", "bg_remover"]