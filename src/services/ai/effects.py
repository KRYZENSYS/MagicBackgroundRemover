"""Special effects: passport photo, product photo, shadow, watermark."""
from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont, ImageOps


class EffectsService:
    async def passport_photo(
        self, img_bytes: bytes, size: tuple[int, int] = (413, 531), background_color: str = "#FFFFFF"
    ) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        # Center-crop to target aspect ratio
        target_ratio = size[0] / size[1]
        src_ratio = img.width / img.height
        if src_ratio > target_ratio:
            new_w = int(img.height * target_ratio)
            left = (img.width - new_w) // 2
            img = img.crop((left, 0, left + new_w, img.height))
        else:
            new_h = int(img.width / target_ratio)
            top = (img.height - new_h) // 2
            img = img.crop((0, top, img.width, top + new_h))
        img = img.resize(size, Image.LANCZOS)
        bg = Image.new("RGB", size, background_color)
        bg.paste(img)
        out = io.BytesIO()
        bg.save(out, format="JPEG", quality=92, optimize=True)
        return out.getvalue()

    async def product_photo(self, img_bytes: bytes) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = ImageOps.autocontrast(img)
        img = img.filter(__import__("PIL.ImageFilter", fromlist=["UnsharpMask"]).UnsharpMask(radius=2, percent=120, threshold=3))
        out = io.BytesIO()
        img.save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def drop_shadow(self, img_bytes: bytes, offset=(20, 20), opacity=80, blur=15) -> bytes:
        from PIL import ImageFilter
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        mask = img.split()[3]
        shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, opacity))
        shadow.paste(shadow_layer, mask=mask)
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
        canvas_w = img.width + abs(offset[0]) + blur * 2
        canvas_h = img.height + abs(offset[1]) + blur * 2
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
        canvas.paste(shadow, (blur + max(offset[0], 0), blur + max(offset[1], 0)), shadow)
        canvas.paste(img, (blur + max(-offset[0], 0), blur + max(-offset[1], 0)), img)
        out = io.BytesIO()
        canvas.convert("RGB").save(out, format="PNG", optimize=True)
        return out.getvalue()

    async def add_text_watermark(self, img_bytes: bytes, text: str, opacity: int = 60) -> bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        try:
            font = ImageFont.truetype("arial.ttf", int(img.height * 0.05))
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (img.width - tw) // 2
        y = (img.height - th) // 2
        draw.text((x, y), text, fill=(255, 255, 255, opacity), font=font)
        out = Image.alpha_composite(img, watermark_layer)
        buf = io.BytesIO()
        out.convert("RGB").save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    async def crop_to_ratio(self, img_bytes: bytes, ratio: str = "1:1") -> bytes:
        ratios = {"1:1": 1, "16:9": 16 / 9, "9:16": 9 / 16, "4:3": 4 / 3, "3:4": 3 / 4}
        target = ratios.get(ratio, 1)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        src_ratio = img.width / img.height
        if src_ratio > target:
            new_w = int(img.height * target)
            left = (img.width - new_w) // 2
            img = img.crop((left, 0, left + new_w, img.height))
        else:
            new_h = int(img.width / target)
            top = (img.height - new_h) // 2
            img = img.crop((0, top, img.width, top + new_h))
        out = io.BytesIO()
        img.save(out, format="PNG", optimize=True)
        return out.getvalue()


effects_service = EffectsService()
__all__ = ["EffectsService", "effects_service"]