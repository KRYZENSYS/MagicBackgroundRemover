"""Generic image processing: resize, compress, rotate, flip, crop."""
from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessor:
    async def resize(
        self,
        img_bytes: bytes,
        width: int | None = None,
        height: int | None = None,
        keep_aspect: bool = True,
    ) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        w, h = img.size
        if width and height and not keep_aspect:
            new_size = (width, height)
        elif width and not height:
            ratio = width / w
            new_size = (width, int(h * ratio))
        elif height and not width:
            ratio = height / h
            new_size = (int(w * ratio), height)
        else:
            return img_bytes
        result = img.resize(new_size, Image.LANCZOS)
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def compress(self, img_bytes: bytes, quality: int = 70) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=quality, optimize=True)
        return out.getvalue()

    async def rotate(self, img_bytes: bytes, degrees: int = 90) -> bytes:
        if degrees not in (90, 180, 270):
            raise ValueError("degrees must be 90, 180, or 270")
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        result = img.rotate(degrees, expand=True)
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def flip(self, img_bytes: bytes, direction: str = "horizontal") -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        if direction == "horizontal":
            result = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif direction == "vertical":
            result = img.transpose(Image.FLIP_TOP_BOTTOM)
        else:
            raise ValueError("direction must be horizontal or vertical")
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def crop(self, img_bytes: bytes, left: int, top: int, right: int, bottom: int) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        result = img.crop((left, top, right, bottom))
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()


image_processor = ImageProcessor()

__all__ = ["ImageProcessor", "image_processor"]