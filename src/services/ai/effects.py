"""Effects: shadow, watermark, passport, product photo."""
from __future__ import annotations

import io
import logging

from PIL import Image, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger(__name__)


class EffectsService:
    async def drop_shadow(self, img_bytes: bytes, offset=(15, 15), blur=10) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        mask = img.split()[3] if img.mode == "RGBA" else None
        shadow.paste(img, offset, mask=mask)
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
        shadow.paste(img, (0, 0), mask=mask)
        out = io.BytesIO()
        shadow.save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def add_text_watermark(self, img_bytes: bytes, text: str = "MagicBG") -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        w, h = img.size
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        try:
            font_size = max(20, w // 20)
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = w - tw - 20
        y = h - th - 20
        draw.text((x, y), text, fill=(255, 255, 255, 180), font=font)
        result = Image.alpha_composite(img, overlay)
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def passport_photo(
        self,
        img_bytes: bytes,
        size: tuple[int, int] = (413, 531),
        background_color: str = "#FFFFFF",
    ) -> bytes:
        """Crop to passport size with white background."""
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        target_w, target_h = size
        target_ratio = target_w / target_h
        w, h = img.size
        src_ratio = w / h
        if src_ratio > target_ratio:
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))
        img = img.resize(size, Image.LANCZOS)
        bg = Image.new("RGB", size, background_color)
        bg.paste(img)
        out = io.BytesIO()
        bg.save(out, format="JPEG", quality=95, optimize=True)
        return out.getvalue()

    async def product_photo(self, img_bytes: bytes) -> bytes:
        """Make product photo: white bg + slight shadow + sharpen."""
        from src.services.ai.bg_remover import bg_remover
        no_bg = await bg_remover.remove_background(img_bytes)
        fg = Image.open(io.BytesIO(no_bg)).convert("RGBA")
        w, h = fg.size
        bg = Image.new("RGBA", (w + 40, h + 40), (255, 255, 255, 255))
        bg.paste(fg, (20, 20), mask=fg.split()[3])
        result = bg.convert("RGB")
        out = io.BytesIO()
        result.save(out, format="PNG", optimize=True)
        return out.getvalue()


effects_service = EffectsService()

__all__ = ["EffectsService", "effects_service"]