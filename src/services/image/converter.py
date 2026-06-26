"""Convert between image formats."""
from __future__ import annotations

import io

from PIL import Image


class ImageConverter:
    FORMATS = {"PNG": "PNG", "JPEG": "JPEG", "WEBP": "WEBP", "BMP": "BMP", "TIFF": "TIFF", "GIF": "GIF"}

    async def convert(self, img_bytes: bytes, target_format: str = "PNG") -> bytes:
        target = target_format.upper().lstrip(".")
        if target not in self.FORMATS:
            raise ValueError(f"Format {target} not supported")
        img = Image.open(io.BytesIO(img_bytes))
        if target == "JPEG" and img.mode != "RGB":
            img = img.convert("RGB")
        elif target == "PNG" and img.mode == "P":
            img = img.convert("RGBA")
        buf = io.BytesIO()
        img.save(buf, format=target)
        return buf.getvalue()

    async def to_pdf(self, img_bytes_list: list[bytes]) -> bytes:
        """Combine multiple images into a single PDF."""
        if not img_bytes_list:
            raise ValueError("Empty image list")
        pil_images = []
        for raw in img_bytes_list:
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            pil_images.append(img)
        buf = io.BytesIO()
        first, *rest = pil_images
        first.save(buf, format="PDF", save_all=True, append_images=rest)
        return buf.getvalue()


image_converter = ImageConverter()
__all__ = ["ImageConverter", "image_converter"]