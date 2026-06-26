"""Face / skin / hair enhancement via GFPGAN (with fallback)."""
from __future__ import annotations

import asyncio
import io
from pathlib import Path

from PIL import Image

from src.config.logging import logger
from src.config.settings import settings
from src.exceptions import ImageProcessingError


class FaceEnhancerService:
    def __init__(self) -> None:
        self._model = None

    async def _load(self):
        if self._model is not None:
            return self._model
        if not settings.ENABLE_GFPGAN:
            return None
        try:
            from gfpgan import GFPGANer

            model_path = Path(settings.STORAGE_DIR) / "models" / "GFPGANv1.4.pth"
            if not model_path.exists():
                return None
            self._model = GFPGANer(
                model_path=str(model_path),
                upscale=1,
                arch="clean",
                channel_multiplier=2,
                bg_upsampler=None,
            )
            return self._model
        except Exception as e:
            logger.warning("GFPGAN unavailable: %s", e)
            return None

    async def enhance_face(self, image_bytes: bytes) -> bytes:
        try:
            model = await self._load()
            if model is None:
                from src.services.ai.enhancer import image_enhancer

                return await image_enhancer.sharpen(image_bytes, amount=1.2)

            import cv2
            import numpy as np

            arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

            def _do():
                _, _, output = model.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
                ok, buf = cv2.imencode(".png", output)
                if not ok:
                    raise ImageProcessingError("encode failed")
                return buf.tobytes()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Face enhance failed: {e}")

    async def hair_refine(self, image_bytes: bytes) -> bytes:
        from src.services.ai.bg_remover import bg_remover
        from src.services.ai.enhancer import image_enhancer

        no_bg = await bg_remover.remove_background(image_bytes)
        return await image_enhancer.smooth_edges(no_bg, iterations=2)


face_enhancer = FaceEnhancerService()


__all__ = ["FaceEnhancerService", "face_enhancer"]