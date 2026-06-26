"""Image format converter (PNG <-> JPG <-> WEBP)."""
from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


class ImageConverter:
    async def convert(self, img_bytes: bytes, target_format: str = "PNG") -> bytes:
        img = Image.open(io.BytesIO(img_bytes))
        target_format = target_format.upper().lstrip(".")
        if target_format == "JPG":
            target_format = "JPEG"
        if img.mode == "RGBA" and target_format in ("JPEG",):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        out = io.BytesIO()
        img.save(out, format=target_format, optimize=True, quality=95)
        return out.getvalue()

    async def to_pdf(self, images: list[bytes]) -> bytes:
        """Combine multiple images into a single PDF."""
        pil_images = []
        for ib in images:
            img = Image.open(io.BytesIO(ib)).convert("RGB")
            pil_images.append(img)
        out = io.BytesIO()
        if pil_images:
            pil_images[0].save(out, format="PDF", save_all=True, append_images=pil_images[1:])
        return out.getvalue()


image_converter = ImageConverter()

__all__ = ["ImageConverter", "image_converter"]