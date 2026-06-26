"""Tests for AI services."""
from __future__ import annotations

import io

import pytest
from PIL import Image

from src.services.ai.enhancer import image_enhancer
from src.services.ai.effects import effects_service
from src.services.ai.validator import image_validator


def _make_png(size=(64, 64), color=(255, 255, 255)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_validator_accepts_valid_png():
    raw = _make_png()
    info = image_validator.inspect(raw)
    assert info["width"] == 64
    assert info["height"] == 64
    assert info["format"] == "PNG"


@pytest.mark.asyncio
async def test_validator_rejects_empty():
    with pytest.raises(ValueError):
        image_validator.inspect(b"")


@pytest.mark.asyncio
async def test_enhancer_works():
    raw = _make_png(color=(200, 100, 50))
    out = await image_enhancer.enhance(raw)
    assert len(out) > 0
    Image.open(io.BytesIO(out))


@pytest.mark.asyncio
async def test_passport_photo():
    raw = _make_png(size=(800, 600))
    out = await effects_service.passport_photo(raw)
    img = Image.open(io.BytesIO(out))
    assert img.size == (413, 531)


@pytest.mark.asyncio
async def test_crop_to_ratio():
    raw = _make_png(size=(800, 400))
    out = await effects_service.crop_to_ratio(raw, "1:1")
    img = Image.open(io.BytesIO(out))
    assert img.size == (400, 400)