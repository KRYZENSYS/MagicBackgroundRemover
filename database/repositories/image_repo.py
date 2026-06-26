"""Image processing history repository."""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ProcessedImage, User


class ImageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(self, user_id: int, tool: str, options: dict, input_size: int,
                     output_size: int, duration_ms: int, success: bool = True,
                     error: Optional[str] = None, file_id: Optional[str] = None) -> ProcessedImage:
        img = ProcessedImage(
            user_id=user_id, tool=tool, options=options,
            input_size=input_size, output_size=output_size,
            duration_ms=duration_ms, success=success, error=error, file_id=file_id,
        )
        self.session.add(img)
        await self.session.commit()
        await self.session.refresh(img)
        return img

    async def user_history(self, user_id: int, limit: int = 50) -> List[ProcessedImage]:
        result = await self.session.execute(
            select(ProcessedImage)
            .where(ProcessedImage.user_id == user_id)
            .order_by(ProcessedImage.processed_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def total_count(self) -> int:
        result = await self.session.execute(select(func.count(ProcessedImage.id)))
        return result.scalar_one()

    async def today_count(self) -> int:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(ProcessedImage.id)).where(ProcessedImage.processed_at >= today_start)
        )
        return result.scalar_one()

    async def avg_duration(self, tool: Optional[str] = None) -> float:
        stmt = select(func.avg(ProcessedImage.duration_ms))
        if tool:
            stmt = stmt.where(ProcessedImage.tool == tool)
        result = await self.session.execute(stmt)
        return float(result.scalar_one() or 0.0)

    async def tool_distribution(self) -> dict:
        result = await self.session.execute(
            select(ProcessedImage.tool, func.count(ProcessedImage.id))
            .group_by(ProcessedImage.tool)
        )
        return {row[0]: row[1] for row in result.all()}