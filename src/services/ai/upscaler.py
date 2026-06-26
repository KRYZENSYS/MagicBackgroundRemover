"""Image upscaling via Real-ESRGAN. Falls back to Lanczos if not installed."""
from __future__ import annotations

import asyncio
import io
from pathlib import Path
from typing import Optional

from PIL import Image

from src.config.logging import logger
from src.config.settings import settings
from src.exceptions import AIServiceError, ImageProcessingError


_ESRGAN_AVAILABLE = False
try:
    from realesrgan import RealESRGAN

    _ESRGAN_AVAILABLE = True
except ImportError:  # pragma: no cover
    RealESRGAN = None  # type: ignore


class UpscalerService:
    """2x/4x/8x upscaling with graceful fallback."""

    def __init__(self) -> None:
        self._model = None
        self._lock = asyncio.Lock()

    async def _get_model(self, scale: int = 4):
        if not _ESRGAN_AVAILABLE:
            return None
        if self._model is None:
            async with self._lock:
                if self._model is None:
                    try:
                        from basicsr.archs.rrdbnet_arch import RRDBNet  # noqa
                        import torch  # noqa

                        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                        model = RealESRGAN(device, scale=4)
                        model.load_weights(
                            str(Path(settings.STORAGE_DIR) / "models" / f"RealESRGAN_x{scale}plus.pth"),
                            download=True,
                        )
                        self._model = model
                    except Exception as e:
                        logger.warning("Real-ESRGAN unavailable, using Lanczos fallback: %s", e)
                        return None
        return self._model

    async def upscale(self, image_bytes: bytes, scale: int = 4) -> bytes:
        if scale not in (2, 4, 8):
            raise ValueError("scale must be 2, 4 or 8")
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            model = await self._get_model(scale=4 if scale <= 4 else 4)
            if model is None:
                def _lanczos():
                    w, h = img.size
                    return img.resize((w * scale, h * scale), Image.LANCZOS)

                out = await asyncio.to_thread(_lanczos)
                buf = io.BytesIO()
                out.save(buf, format="PNG")
                return buf.getvalue()

            def _do():
                out = model.predict(img.convert("RGB"))
                buf = io.BytesIO()
                out.save(buf, format="PNG")
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            logger.exception("Upscale failed")
            raise ImageProcessingError(f"Upscale failed: {e}")

    async def upscale_2x(self, image_bytes: bytes) -> bytes:
        return await self.upscale(image_bytes, scale=2)

    async def upscale_4x(self, image_bytes: bytes) -> bytes:
        return await self.upscale(image_bytes, scale=4)

    async def upscale_8x(self, image_bytes: bytes) -> bytes:
        # 8x is approximated as 2x of 4x for safety
        x4 = await self.upscale(image_bytes, scale=4)
        return await self.upscale(x4, scale=2)


upscaler = UpscalerService()


__all__ = ["UpscalerService", "upscaler"]