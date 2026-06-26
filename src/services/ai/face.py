"""Face enhancement using GFPGAN if available, else plain upscaling + sharpening."""
from __future__ import annotations

import io

from PIL import Image, ImageEnhance, ImageFilter

from src.config.logging import logger


class FaceEnhancer:
    def __init__(self):
        self._has_gfpgan = False
        try:
            import gfpgan  # noqa: F401
            self._has_gfpgan = True
        except ImportError:
            logger.warning("GFPGAN not installed; using PIL fallback for face enhancement.")

    async def enhance_face(self, img_bytes: bytes) -> bytes:
        if self._has_gfpgan:
            try:
                return await self._gfpgan_enhance(img_bytes)
            except Exception as e:
                logger.warning("GFPGAN failed, falling back: %s", e)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        img = ImageEnhance.Contrast(img).enhance(1.1)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    async def _gfpgan_enhance(self, img_bytes: bytes) -> bytes:
        import asyncio
        import numpy as np
        from gfpgan import GFPGANer  # type: ignore
        from src.services.ai.model_manager import model_manager

        model = await model_manager.get(
            "gfpgan",
            lambda: GFPGANer(model_path="gfpgan/weights/GFPGANv1.4.pth", upscale=2, arch="clean", channel_multiplier=2),
        )
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        _, _, out = await asyncio.to_thread(model.enhance, np.array(img), has_aligned=False, only_center_face=False, paste_back=True)
        buf = io.BytesIO()
        Image.fromarray(out).save(buf, format="PNG", optimize=True)
        return buf.getvalue()


face_enhancer = FaceEnhancer()
__all__ = ["FaceEnhancer", "face_enhancer"]