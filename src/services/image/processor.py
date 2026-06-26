"""Generic image processing: resize, compress, rotate, flip, crop."""
from __future__ import annotations

import io

from PIL import Image


class ImageProcessor:
    async def resize(
        self,
        img_bytes: bytes,
        width: int | None = None,
        height: int | None = None,
        keep_aspect: bool = True,
    ) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        if keep_aspect:
            if width and height:
                img.thumbnail((width, height), Image.LANCZOS)
            elif width:
                h = int(img.height * (width / img.width))
                img = img.resize((width, h), Image.LANCZOS)
            elif height:
                w = int(img.width * (height / img.height))
                img = img.resize((w, height), Image.LANCZOS)
        else:
            img = img.resize((width or img.width, height or img.height), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    async def compress(self, img_bytes: bytes, quality: int = 70) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()

    async def rotate(self, img_bytes: bytes, degrees: int = 90) -> bytes:
        if degrees not in (90, 180, 270):
            raise ValueError("degrees must be 90, 180 or 270")
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = img.rotate(-degrees, expand=True)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    async def flip(self, img_bytes: bytes, direction: str = "horizontal") -> bytes:
        if direction not in ("horizontal", "vertical"):
            raise ValueError("direction must be horizontal or vertical")
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        if direction == "horizontal":
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        else:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    async def crop(
        self, img_bytes: bytes, left: int, top: int, right: int, bottom: int
    ) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = img.crop((left, top, right, bottom))
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()


image_processor = ImageProcessor()
__all__ = ["ImageProcessor", "image_processor"]