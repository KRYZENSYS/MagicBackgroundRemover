"""Image upscaler. Tries Real-ESRGAN; falls back to LANCZOS."""
from __future__ import annotations

import io

from PIL import Image

from src.config.logging import logger


class Upscaler:
    def __init__(self):
        self._has_realesrgan = False
        try:
            import realesrgan  # noqa: F401
            self._has_realesrgan = True
        except ImportError:
            logger.warning("Real-ESRGAN not installed; using PIL LANCZOS fallback.")

    async def upscale(self, img_bytes: bytes, factor: int = 2) -> bytes:
        if factor not in (2, 4):
            raise ValueError("factor must be 2 or 4")
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        new_size = (img.width * factor, img.height * factor)
        if self._has_realesrgan:
            try:
                return await self._realesrgan_upscale(img_bytes, factor)
            except Exception as e:
                logger.warning("Real-ESRGAN failed, falling back to LANCZOS: %s", e)
        result = img.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        result.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    async def _realesrgan_upscale(self, img_bytes: bytes, factor: int) -> bytes:
        import asyncio
        from PIL import Image
        from basicsr.archs.rrdbnet_arch import RRDBNet  # type: ignore
        from realesrgan import RealESRGANer  # type: ignore
        from src.services.ai.model_manager import model_manager

        model_name = f"realesrgan_x{factor}"
        model = await model_manager.get(
            model_name,
            lambda: RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=factor),
        )
        upsampler = RealESRGANer(
            scale=factor,
            model_path=str(model),
            model=model,
            tile=256,
            tile_pad=10,
            pre_pad=0,
            half=False,
        )
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        import numpy as np
        out, _ = await asyncio.to_thread(upsampler.enhance, np.array(img), outscale=factor)
        buf = io.BytesIO()
        Image.fromarray(out).save(buf, format="PNG", optimize=True)
        return buf.getvalue()


upscaler = Upscaler()
__all__ = ["Upscaler", "upscaler"]