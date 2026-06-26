"""Validate uploaded images before heavy processing."""
from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from src.constants import MAX_IMAGE_BYTES, MAX_IMAGE_DIMENSION, MIN_IMAGE_DIMENSION, ALLOWED_IMAGE_FORMATS


class ImageValidator:
    def inspect(self, raw: bytes) -> dict:
        if not raw:
            raise ValueError("Bo'sh fayl.")
        if len(raw) > MAX_IMAGE_BYTES:
            raise ValueError(f"Fayl juda katta: {len(raw)//1024//1024}MB > {MAX_IMAGE_BYTES//1024//1024}MB")
        try:
            with Image.open(io.BytesIO(raw)) as im:
                im.verify()
        except (UnidentifiedImageError, Exception) as e:
            raise ValueError(f"Rasm formati noto'g'ri: {e}") from e

        try:
            with Image.open(io.BytesIO(raw)) as im:
                im.load()
                w, h = im.size
                fmt = im.format
                mode = im.mode
        except Exception as e:
            raise ValueError(f"Rasm o'qib bo'lmadi: {e}") from e

        if fmt not in ALLOWED_IMAGE_FORMATS:
            raise ValueError(f"Format {fmt} qo'llab-quvvatlanmaydi. Ruxsat: {', '.join(ALLOWED_IMAGE_FORMATS)}")
        if max(w, h) > MAX_IMAGE_DIMENSION:
            raise ValueError(f"O'lcham juda katta: {w}x{h}. Maks: {MAX_IMAGE_DIMENSION}px")
        if min(w, h) < MIN_IMAGE_DIMENSION:
            raise ValueError(f"O'lcham juda kichik: {w}x{h}. Min: {MIN_IMAGE_DIMENSION}px")
        return {"width": w, "height": h, "format": fmt, "mode": mode, "size": len(raw)}

    def normalize(self, raw: bytes) -> bytes:
        """Strip metadata, convert to RGB if needed."""
        with Image.open(io.BytesIO(raw)) as im:
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGB")
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=True)
            return buf.getvalue()


image_validator = ImageValidator()

__all__ = ["ImageValidator", "image_validator"]