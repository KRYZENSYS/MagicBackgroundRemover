"""AI image processing service — background removal, enhancement, transforms."""
import io
import time
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from rembg import remove as rembg_remove

from core.logger import logger
from core.exceptions import ProcessingError, InvalidImageError


class ImageProcessor:
    """Async wrapper around image processing operations."""

    @staticmethod
    async def load(data: bytes) -> Image.Image:
        try:
            return Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception as e:
            raise InvalidImageError(f"Cannot open image: {e}")

    @staticmethod
    async def save(image: Image.Image, fmt: str = "PNG", quality: int = 95) -> bytes:
        buf = io.BytesIO()
        if fmt.upper() == "JPEG" and image.mode == "RGBA":
            image = image.convert("RGB")
        image.save(buf, format=fmt, quality=quality)
        return buf.getvalue()

    @staticmethod
    async def remove_background(data: bytes, model: str = "u2net") -> bytes:
        """Remove background using rembg."""
        try:
            img = Image.open(io.BytesIO(data)).convert("RGBA")
            out = rembg_remove(img)
            return await ImageProcessor.save(out, "PNG")
        except Exception as e:
            logger.error(f"BG remove failed: {e}")
            raise ProcessingError(f"Background removal failed: {e}")

    @staticmethod
    async def replace_background(data: bytes, bg_color: Tuple[int, int, int] = (255, 255, 255)) -> bytes:
        """Replace transparent background with solid color."""
        cut = await ImageProcessor.remove_background(data)
        cut_img = Image.open(io.BytesIO(cut)).convert("RGBA")
        bg = Image.new("RGBA", cut_img.size, bg_color + (255,))
        bg.paste(cut_img, mask=cut_img.split()[3])
        return await ImageProcessor.save(bg.convert("RGB"), "PNG")

    @staticmethod
    async def gradient_background(data: bytes, color_a: Tuple[int, int, int] = (0, 0, 0),
                                   color_b: Tuple[int, int, int] = (255, 255, 255),
                                   direction: str = "vertical") -> bytes:
        cut = await ImageProcessor.remove_background(data)
        cut_img = Image.open(io.BytesIO(cut)).convert("RGBA")
        w, h = cut_img.size
        gradient = Image.new("RGB", (w, h))
        for y in range(h):
            for x in range(w):
                if direction == "vertical":
                    ratio = y / h
                else:
                    ratio = x / w
                color = tuple(int(a + (b - a) * ratio) for a, b in zip(color_a, color_b))
                gradient.putpixel((x, y), color)
        gradient.paste(cut_img, mask=cut_img.split()[3])
        return await ImageProcessor.save(gradient, "PNG")

    @staticmethod
    async def upscale(data: bytes, factor: int = 2) -> bytes:
        """High-quality upscale."""
        img = await ImageProcessor.load(data)
        new_size = (img.size[0] * factor, img.size[1] * factor)
        return await ImageProcessor.save(img.resize(new_size, Image.LANCZOS))

    @staticmethod
    async def resize(data: bytes, width: int, height: int, keep_aspect: bool = True) -> bytes:
        img = await ImageProcessor.load(data)
        if keep_aspect:
            img.thumbnail((width, height), Image.LANCZOS)
        else:
            img = img.resize((width, height), Image.LANCZOS)
        return await ImageProcessor.save(img)

    @staticmethod
    async def compress(data: bytes, quality: int = 75) -> bytes:
        img = await ImageProcessor.load(data)
        if img.mode == "RGBA":
            return await ImageProcessor.save(img, "WEBP", quality)
        return await ImageProcessor.save(img.convert("RGB"), "JPEG", quality)

    @staticmethod
    async def convert(data: bytes, target_format: str = "PNG") -> bytes:
        img = await ImageProcessor.load(data)
        return await ImageProcessor.save(img, target_format)

    @staticmethod
    async def rotate(data: bytes, angle: float) -> bytes:
        img = await ImageProcessor.load(data)
        return await ImageProcessor.save(img.rotate(angle, expand=True))

    @staticmethod
    async def flip(data: bytes, direction: str = "horizontal") -> bytes:
        img = await ImageProcessor.load(data)
        if direction == "horizontal":
            return await ImageProcessor.save(ImageOps.mirror(img))
        return await ImageProcessor.save(ImageOps.flip(img))

    @staticmethod
    async def enhance(data: bytes, factor: float = 1.5) -> bytes:
        """Generic enhancement: contrast, color, sharpness."""
        img = await ImageProcessor.load(data)
        img = ImageEnhance.Contrast(img).enhance(factor)
        img = ImageEnhance.Color(img).enhance(factor)
        img = ImageEnhance.Sharpness(img).enhance(factor)
        return await ImageProcessor.save(img)

    @staticmethod
    async def sharpen(data: bytes, factor: float = 2.0) -> bytes:
        img = await ImageProcessor.load(data)
        return await ImageProcessor.save(img.filter(ImageFilter.UnsharpMask(radius=2, percent=int(factor * 100), threshold=3)))

    @staticmethod
    async def denoise(data: bytes) -> bytes:
        img = await ImageProcessor.load(data)
        return await ImageProcessor.save(img.filter(ImageFilter.SMOOTH))

    @staticmethod
    async def blur_background(data: bytes, strength: int = 15) -> bytes:
        """Portrait mode: blur background."""
        cut = await ImageProcessor.remove_background(data)
        cut_img = Image.open(io.BytesIO(cut)).convert("RGBA")
        mask = cut_img.split()[3]
        bg = Image.new("RGB", cut_img.size, (240, 240, 240))
        blurred_bg = bg.filter(ImageFilter.GaussianBlur(strength))
        blurred_bg.paste(cut_img, mask=mask)
        return await ImageProcessor.save(blurred_bg)

    @staticmethod
    async def auto_crop(data: bytes) -> bytes:
        """Crop transparent borders."""
        img = await ImageProcessor.load(data)
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        return await ImageProcessor.save(img)

    @staticmethod
    async def add_watermark(data: bytes, text: str, opacity: int = 100) -> bytes:
        img = await ImageProcessor.load(data).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(txt_layer)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(img.size[1] * 0.08))
            except Exception:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pos = ((img.size[0] - w) // 2, img.size[1] - h - 20)
            draw.text(pos, text, fill=(255, 255, 255, opacity), font=font)
            return await ImageProcessor.save(Image.alpha_composite(img, txt_layer))
        except Exception as e:
            logger.warning(f"Watermark failed: {e}")
            return data

    @staticmethod
    async def passport_photo(data: bytes, size: Tuple[int, int] = (413, 531), bg: Tuple[int, int, int] = (255, 255, 255)) -> bytes:
        """Passport photo with white background and specific dimensions."""
        cut = await ImageProcessor.remove_background(data)
        cut_img = Image.open(io.BytesIO(cut)).convert("RGBA")
        ratio = size[0] / size[1]
        cut_ratio = cut_img.size[0] / cut_img.size[1]
        if cut_ratio > ratio:
            new_h = size[1]
            new_w = int(new_h * cut_ratio)
        else:
            new_w = size[0]
            new_h = int(new_w / cut_ratio)
        cut_img = cut_img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - size[0]) // 2
        top = (new_h - size[1]) // 2
        cut_img = cut_img.crop((left, top, left + size[0], top + size[1]))
        bg_img = Image.new("RGB", size, bg)
        bg_img.paste(cut_img, mask=cut_img.split()[3])
        return await ImageProcessor.save(bg_img, "JPEG", quality=95)

    @staticmethod
    async def metadata(data: bytes) -> dict:
        """Extract image metadata."""
        img = Image.open(io.BytesIO(data))
        info = {"format": img.format, "size": img.size, "mode": img.mode}
        if hasattr(img, "info"):
            info["info"] = {k: str(v)[:200] for k, v in img.info.items()}
        return info

    @staticmethod
    async def time_it(coro):
        """Run a coroutine and return (result, duration_ms)."""
        start = time.perf_counter()
        result = await coro
        return result, int((time.perf_counter() - start) * 1000)