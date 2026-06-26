"""Background removal service powered by rembg (U-2-Net, ISNet, etc.)."""
from __future__ import annotations

import asyncio
import io
from typing import Optional

import numpy as np
from PIL import Image
from rembg import new_session, remove

from src.config.logging import logger
from src.config.settings import settings
from src.constants import AIModel, BackgroundColor
from src.exceptions import AIServiceError, ImageProcessingError


# Lazy-loaded sessions - rembg models are heavy (~170MB).
class BackgroundRemoverService:
    def __init__(self) -> None:
        self._sessions: dict[str, object] = {}
        self._lock = asyncio.Lock()

    async def _get_session(self, model: AIModel):
        key = model.value
        if key not in self._sessions:
            async with self._lock:
                if key not in self._sessions:
                    logger.info("Loading rembg model %s...", key)
                    try:
                        self._sessions[key] = await asyncio.to_thread(new_session, key)
                    except Exception as e:
                        logger.error("Failed to load model %s: %s", key, e)
                        raise AIServiceError(f"Model load failed: {e}")
        return self._sessions[key]

    async def remove_background(
        self,
        image_bytes: bytes,
        model: Optional[AIModel] = None,
        only_mask: bool = False,
        alpha_matting: bool = False,
        alpha_matting_foreground_threshold: int = 240,
        alpha_matting_background_threshold: int = 10,
        alpha_matting_erode_size: int = 10,
    ) -> bytes:
        model = model or AIModel(settings.REMBG_MODEL.value if hasattr(settings.REMBG_MODEL, "value") else settings.REMBG_MODEL)
        if isinstance(model, str):
            model = AIModel(model)
        session = await self._get_session(model)
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.load()

            def _do_remove() -> bytes:
                buf = io.BytesIO()
                out = remove(
                    img,
                    session=session,
                    only_mask=only_mask,
                    alpha_matting=alpha_matting,
                    alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                    alpha_matting_background_threshold=alpha_matting_background_threshold,
                    alpha_matting_erode_size=alpha_matting_erode_size,
                )
                if isinstance(out, Image.Image):
                    out.save(buf, format="PNG")
                else:
                    # numpy mask
                    Image.fromarray((out * 255).astype("uint8")).save(buf, format="PNG")
                return buf.getvalue()

            return await asyncio.to_thread(_do_remove)
        except ImageProcessingError:
            raise
        except Exception as e:
            logger.exception("Background removal failed: %s", e)
            raise ImageProcessingError(f"Bg removal failed: {e}")

    async def replace_background(
        self,
        image_bytes: bytes,
        new_bg: Image.Image,
        model: Optional[AIModel] = None,
    ) -> bytes:
        """Remove bg, then composite onto a new background."""
        no_bg = await self.remove_background(image_bytes, model=model)
        subject = Image.open(io.BytesIO(no_bg)).convert("RGBA")
        # Resize bg to subject size
        bg = new_bg.convert("RGB").resize(subject.size)
        bg.paste(subject, mask=subject.split()[-1])
        out = io.BytesIO()
        bg.save(out, format="PNG")
        return out.getvalue()

    async def solid_color_background(
        self,
        image_bytes: bytes,
        color: str = BackgroundColor.WHITE.value,
        model: Optional[AIModel] = None,
    ) -> bytes:
        if color == BackgroundColor.TRANSPARENT.value:
            return await self.remove_background(image_bytes, model=model)
        no_bg = await self.remove_background(image_bytes, model=model)
        subject = Image.open(io.BytesIO(no_bg)).convert("RGBA")
        bg = Image.new("RGB", subject.size, color)
        bg.paste(subject, mask=subject.split()[-1])
        out = io.BytesIO()
        bg.save(out, format="PNG")
        return out.getvalue()

    async def gradient_background(
        self,
        image_bytes: bytes,
        color_a: str = "#FFFFFF",
        color_b: str = "#000000",
        direction: str = "vertical",
        model: Optional[AIModel] = None,
    ) -> bytes:
        no_bg = await self.remove_background(image_bytes, model=model)
        subject = Image.open(io.BytesIO(no_bg)).convert("RGBA")
        w, h = subject.size

        def _gradient():
            top = tuple(int(color_a.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
            bot = tuple(int(color_b.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
            arr = np.zeros((h, w, 3), dtype=np.uint8)
            if direction == "vertical":
                for y in range(h):
                    ratio = y / max(h - 1, 1)
                    arr[y, :, 0] = int(top[0] * (1 - ratio) + bot[0] * ratio)
                    arr[y, :, 1] = int(top[1] * (1 - ratio) + bot[1] * ratio)
                    arr[y, :, 2] = int(top[2] * (1 - ratio) + bot[2] * ratio)
            else:
                for x in range(w):
                    ratio = x / max(w - 1, 1)
                    arr[:, x, 0] = int(top[0] * (1 - ratio) + bot[0] * ratio)
                    arr[:, x, 1] = int(top[1] * (1 - ratio) + bot[1] * ratio)
                    arr[:, x, 2] = int(top[2] * (1 - ratio) + bot[2] * ratio)
            return Image.fromarray(arr)

        bg = await asyncio.to_thread(_gradient)
        bg.paste(subject, mask=subject.split()[-1])
        out = io.BytesIO()
        bg.save(out, format="PNG")
        return out.getvalue()


bg_remover = BackgroundRemoverService()


__all__ = ["BackgroundRemoverService", "bg_remover"]