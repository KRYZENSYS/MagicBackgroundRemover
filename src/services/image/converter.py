"""Image format converter."""
from __future__ import annotations

import asyncio
import io
from typing import Literal

from PIL import Image

from src.exceptions import ImageProcessingError

Format = Literal["PNG", "JPEG", "WEBP", "BMP", "TIFF", "GIF"]


class ImageConverter:
    @staticmethod
    async def convert(image_bytes: bytes, target: Format = "PNG", quality: int = 95) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))

            def _do():
                if target == "JPEG" and img.mode in ("RGBA", "P", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode in ("RGBA", "LA"):
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img.convert("RGBA"))
                    out = background
                elif target == "PNG" and img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                    out = img.convert("RGBA")
                else:
                    out = img
                buf = io.BytesIO()
                save_kwargs = {"format": target}
                if target in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = quality
                out.save(buf, **save_kwargs)
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Convert failed: {e}")


image_converter = ImageConverter()


__all__ = ["ImageConverter", "image_converter"]