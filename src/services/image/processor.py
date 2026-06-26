"""Generic image operations: resize, rotate, flip, crop, compress."""
from __future__ import annotations

import asyncio
import io
from typing import Optional

from PIL import Image

from src.exceptions import ImageProcessingError


class ImageProcessor:
    """All non-AI image manipulations."""

    @staticmethod
    async def resize(
        image_bytes: bytes,
        width: Optional[int] = None,
        height: Optional[int] = None,
        keep_aspect: bool = True,
        quality: int = 95,
    ) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))

            def _do():
                w, h = img.size
                if keep_aspect:
                    if width and not height:
                        ratio = width / w
                        height = int(h * ratio)
                    elif height and not width:
                        ratio = height / h
                        width = int(w * ratio)
                    elif width and height:
                        ratio = min(width / w, height / h)
                        width, height = int(w * ratio), int(h * ratio)
                else:
                    width = width or w
                    height = height or h
                resized = img.resize((width, height), Image.LANCZOS)
                buf = io.BytesIO()
                fmt = img.format or "PNG"
                save_kwargs = {"format": fmt}
                if fmt.upper() in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = quality
                resized.save(buf, **save_kwargs)
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Resize failed: {e}")

    @staticmethod
    async def rotate(image_bytes: bytes, degrees: float = 90.0, expand: bool = True) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))

            def _do():
                out = img.rotate(-degrees, expand=expand, resample=Image.BICUBIC)
                buf = io.BytesIO()
                out.save(buf, format=img.format or "PNG")
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Rotate failed: {e}")

    @staticmethod
    async def flip(image_bytes: bytes, direction: str = "horizontal") -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))

            def _do():
                if direction == "horizontal":
                    out = img.transpose(Image.FLIP_LEFT_RIGHT)
                elif direction == "vertical":
                    out = img.transpose(Image.FLIP_TOP_BOTTOM)
                else:
                    raise ValueError("direction must be horizontal or vertical")
                buf = io.BytesIO()
                out.save(buf, format=img.format or "PNG")
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Flip failed: {e}")

    @staticmethod
    async def crop(
        image_bytes: bytes,
        left: int,
        top: int,
        right: int,
        bottom: int,
    ) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))

            def _do():
                w, h = img.size
                left = max(0, left)
                top = max(0, top)
                right = min(w, right)
                bottom = min(h, bottom)
                if right <= left or bottom <= top:
                    raise ImageProcessingError("Invalid crop rectangle")
                out = img.crop((left, top, right, bottom))
                buf = io.BytesIO()
                out.save(buf, format=img.format or "PNG")
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Crop failed: {e}")

    @staticmethod
    async def compress(image_bytes: bytes, quality: int = 70) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))

            def _do():
                if img.mode in ("RGBA", "P"):
                    img2 = img.convert("RGB")
                else:
                    img2 = img
                buf = io.BytesIO()
                img2.save(buf, format="JPEG", quality=quality, optimize=True)
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Compress failed: {e}")

    @staticmethod
    async def metadata(image_bytes: bytes) -> dict:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return {
                "format": img.format,
                "mode": img.mode,
                "size": list(img.size),
                "info": {k: str(v)[:500] for k, v in img.info.items() if isinstance(v, (str, int, float))},
                "file_size": len(image_bytes),
            }
        except Exception as e:
            raise ImageProcessingError(f"Metadata read failed: {e}")


image_processor = ImageProcessor()


__all__ = ["ImageProcessor", "image_processor"]