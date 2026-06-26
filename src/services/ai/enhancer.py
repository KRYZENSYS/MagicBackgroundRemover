"""Image enhancement: denoise, sharpen, color correction, edge smoothing."""
from __future__ import annotations

import asyncio
import io

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from src.exceptions import ImageProcessingError


class ImageEnhancerService:
    """CPU-based enhancement ops using OpenCV + Pillow."""

    @staticmethod
    async def _to_array(img: Image.Image) -> np.ndarray:
        return await asyncio.to_thread(np.array, img)

    @staticmethod
    async def _from_array(arr: np.ndarray) -> Image.Image:
        return await asyncio.to_thread(Image.fromarray, arr)

    async def enhance(
        self,
        image_bytes: bytes,
        brightness: float = 1.05,
        contrast: float = 1.1,
        saturation: float = 1.1,
        sharpness: float = 1.05,
    ) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            def _do():
                img2 = ImageEnhance.Brightness(img).enhance(brightness)
                img2 = ImageEnhance.Contrast(img2).enhance(contrast)
                img2 = ImageEnhance.Color(img2).enhance(saturation)
                img2 = ImageEnhance.Sharpness(img2).enhance(sharpness)
                buf = io.BytesIO()
                img2.save(buf, format="PNG")
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Enhance failed: {e}")

    async def denoise(self, image_bytes: bytes, strength: int = 7) -> bytes:
        try:
            arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

            def _do():
                out = cv2.fastNlMeansDenoisingColored(img, None, strength, strength, 7, 21)
                ok, buf = cv2.imencode(".png", out)
                if not ok:
                    raise ImageProcessingError("encode failed")
                return buf.tobytes()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Denoise failed: {e}")

    async def sharpen(self, image_bytes: bytes, amount: float = 1.5) -> bytes:
        try:
            arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

            def _do():
                blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=3)
                sharp = cv2.addWeighted(img, amount, blurred, 1 - amount, 0)
                ok, buf = cv2.imencode(".png", sharp)
                if not ok:
                    raise ImageProcessingError("encode failed")
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Sharpen failed: {e}")

    async def auto_color(self, image_bytes: bytes) -> bytes:
        """Auto white-balance and color correction."""
        try:
            arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

            def _do():
                lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                merged = cv2.merge((cl, a, b))
                out = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
                ok, buf = cv2.imencode(".png", out)
                if not ok:
                    raise ImageProcessingError("encode failed")
                return buf.tobytes()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Auto color failed: {e}")

    async def smooth_edges(self, image_bytes: bytes, iterations: int = 1) -> bytes:
        """Smooth alpha channel edges for cleaner cut-outs."""
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

            def _do():
                arr = np.array(img)
                alpha = arr[:, :, 3]
                kernel = np.ones((3, 3), np.uint8)
                smoothed = cv2.GaussianBlur(alpha, (3, 3), 0)
                # Erode/dilate for hairline cleanup
                for _ in range(iterations):
                    smoothed = cv2.dilate(smoothed, kernel, iterations=1)
                    smoothed = cv2.erode(smoothed, kernel, iterations=1)
                    smoothed = cv2.GaussianBlur(smoothed, (3, 3), 0)
                arr[:, :, 3] = smoothed
                out = Image.fromarray(arr)
                buf = io.BytesIO()
                out.save(buf, format="PNG")
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Smooth edges failed: {e}")

    async def crop_transparent(self, image_bytes: bytes, padding: int = 0) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

            def _do():
                arr = np.array(img)
                alpha = arr[:, :, 3]
                mask = alpha > 0
                if not mask.any():
                    return image_bytes
                rows = np.any(mask, axis=1)
                cols = np.any(mask, axis=0)
                rmin, rmax = np.where(rows)[0][[0, -1]]
                cmin, cmax = np.where(cols)[0][[0, -1]]
                rmin = max(0, rmin - padding)
                cmin = max(0, cmin - padding)
                rmax = min(arr.shape[0], rmax + padding + 1)
                cmax = min(arr.shape[1], cmax + padding + 1)
                cropped = arr[rmin:rmax, cmin:cmax]
                out = Image.fromarray(cropped)
                buf = io.BytesIO()
                out.save(buf, format="PNG")
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Crop transparent failed: {e}")

    async def center_object(
        self,
        image_bytes: bytes,
        target_size: tuple[int, int],
        background_color: str = "#FFFFFF",
    ) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

            def _do():
                # Determine object bounding box
                arr = np.array(img)
                alpha = arr[:, :, 3]
                mask = alpha > 0
                if not mask.any():
                    return image_bytes
                rows = np.any(mask, axis=1)
                cols = np.any(mask, axis=0)
                rmin, rmax = np.where(rows)[0][[0, -1]]
                cmin, cmax = np.where(cols)[0][[0, -1]]
                cropped = img.crop((cmin, rmin, cmax + 1, rmax + 1))
                tw, th = target_size
                cw, ch = cropped.size
                scale = min(tw / cw, th / ch) * 0.95
                new_w, new_h = max(1, int(cw * scale)), max(1, int(ch * scale))
                resized = cropped.resize((new_w, new_h), Image.LANCZOS)
                bg_color = tuple(int(background_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
                bg = Image.new("RGBA", target_size, bg_color + (255,))
                x = (tw - new_w) // 2
                y = (th - new_h) // 2
                bg.paste(resized, (x, y), mask=resized.split()[-1])
                buf = io.BytesIO()
                bg.convert("RGB").save(buf, format="PNG")
                return buf.getvalue()

            return await asyncio.to_thread(_do)
        except Exception as e:
            raise ImageProcessingError(f"Center object failed: {e}")

    async def blur_background(self, image_bytes: bytes, blur_strength: int = 35) -> bytes:
        """Portrait-style background blur. Removes bg first, then re-composites blurred."""
        from src.services.ai.bg_remover import bg_remover

        no_bg = await bg_remover.remove_background(image_bytes)
        subject = Image.open(io.BytesIO(no_bg)).convert("RGBA")
        # Blur the original
        orig = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        blurred = orig.filter(ImageFilter.GaussianBlur(radius=blur_strength))
        blurred = blurred.resize(subject.size)
        blurred.paste(subject, mask=subject.split()[-1])
        buf = io.BytesIO()
        blurred.save(buf, format="PNG")
        return buf.getvalue()


image_enhancer = ImageEnhancerService()


__all__ = ["ImageEnhancerService", "image_enhancer"]