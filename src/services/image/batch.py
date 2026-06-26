"""Batch image processing and ZIP packaging."""
from __future__ import annotations

import asyncio
import io
import zipfile
from dataclasses import dataclass
from typing import Awaitable, Callable

from src.constants import MAX_BATCH_FILES


@dataclass
class BatchResult:
    name: str
    data: bytes
    success: bool
    error: str | None = None


class BatchProcessor:
    async def run(
        self,
        items: list[tuple[str, bytes]],
        handler: Callable[[bytes], Awaitable[bytes]],
        max_concurrency: int = 3,
    ) -> list[BatchResult]:
        if len(items) > MAX_BATCH_FILES:
            raise ValueError(f"Batch too large ({len(items)}). Max: {MAX_BATCH_FILES}")
        sem = asyncio.Semaphore(max_concurrency)

        async def _one(name: str, data: bytes) -> BatchResult:
            try:
                async with sem:
                    out = await handler(data)
                    return BatchResult(name=name, data=out, success=True)
            except Exception as e:
                return BatchResult(name=name, data=b"", success=False, error=str(e)[:200])

        results = await asyncio.gather(*[_one(name, data) for name, data in items])
        return list(results)

    @staticmethod
    def zip_results(results: list[BatchResult]) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            ok = 0
            for r in results:
                if not r.success:
                    continue
                ok += 1
                ext = ".png"
                base = r.name.rsplit(".", 1)[0] if "." in r.name else r.name
                zf.writestr(f"{base}_processed{ext}", r.data)
            zf.writestr("summary.txt", f"Processed: {ok}/{len(results)}\n".encode())
        return buf.getvalue()


batch_processor = BatchProcessor()


__all__ = ["BatchProcessor", "batch_processor", "BatchResult"]