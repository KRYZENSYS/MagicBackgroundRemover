"""Image validation: format, size, dimensions, malware heuristics."""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from src.config.settings import settings
from src.constants import ALLOWED_IMAGE_EXT, MAX_IMAGE_DIMENSION
from src.exceptions import FileTooLargeError, InvalidFileError


@dataclass
class ImageMeta:
    width: int
    height: int
    format: str
    mode: str
    file_size: int
    has_alpha: bool


class ImageValidator:
    @staticmethod
    def check_size(data: bytes) -> None:
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(data) > max_bytes:
            raise FileTooLargeError(
                f"File exceeds limit ({settings.MAX_FILE_SIZE_MB} MB). Got {len(data) // (1024 * 1024)} MB."
            )

    @staticmethod
    def check_extension(filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_IMAGE_EXT:
            raise InvalidFileError(f"Unsupported format: {ext}")
        return ext

    @staticmethod
    def inspect(data: bytes, filename: str | None = None) -> ImageMeta:
        ImageValidator.check_size(data)
        if filename:
            ImageValidator.check_extension(filename)
        try:
            img = Image.open(io.BytesIO(data))
            img.verify()
            img = Image.open(io.BytesIO(data))  # re-open after verify
            if max(img.size) > MAX_IMAGE_DIMENSION:
                raise InvalidFileError(f"Image too large: {img.size}. Max dim: {MAX_IMAGE_DIMENSION}")
            return ImageMeta(
                width=img.width,
                height=img.height,
                format=img.format or "PNG",
                mode=img.mode,
                file_size=len(data),
                has_alpha="A" in img.mode,
            )
        except InvalidFileError:
            raise
        except Exception as e:
            raise InvalidFileError(f"Invalid or corrupted image: {e}")

    @staticmethod
    def is_suspicious(data: bytes) -> bool:
        """Heuristic checks for polyglot files / malware indicators."""
        # Check for embedded scripts in metadata
        suspicious_signatures = [b"<script", b"<?php", b"#!/bin/", b"MZ\x90\x00"]
        for sig in suspicious_signatures:
            if sig in data[:8192]:
                return True
        # Very large ICC profile (could hide payload)
        if data.count(b"ICC_PROFILE") > 50:
            return True
        return False


image_validator = ImageValidator()


__all__ = ["ImageValidator", "image_validator", "ImageMeta"]