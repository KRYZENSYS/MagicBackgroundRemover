"""Orqa fonni o'chirish - rembg"""
import io
from rembg import remove
from PIL import Image


async def remove_background(image_bytes: bytes) -> bytes:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        out = remove(img)
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        raise Exception(f"BG error: {e}")