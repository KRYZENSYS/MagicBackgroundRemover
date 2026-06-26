"""FastAPI REST API."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.settings import settings
from core.logger import logger
from database.engine import init_db, close_db
from database.repositories.user_repo import UserRepository
from database.repositories.image_repo import ImageRepository
from database.repositories.payment_repo import PaymentRepository
from database.engine import async_session
from services.image_processor import ImageProcessor
from services.storage import storage
from services.cache import cache
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("API server started")
    yield
    await close_db()
    await cache.close()
    logger.info("API server stopped")


app = FastAPI(
    title="MagicBackground Remover Pro API",
    description="REST API for AI image processing",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= SCHEMAS =============
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str


class StatsResponse(BaseModel):
    users_total: int
    images_total: int
    revenue_total: float


class ProcessResponse(BaseModel):
    success: bool
    file_id: str | None = None
    url: str | None = None
    duration_ms: int = 0


# ============= ENDPOINTS =============

@app.get("/", response_model=HealthResponse, tags=["System"])
async def root():
    return HealthResponse(status="ok", version="2.0.0", database=settings.DATABASE_URL.split("://")[0])


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Health check for load balancers."""
    try:
        async with async_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
    return HealthResponse(status="ok", version="2.0.0", database=db_status)


@app.get("/api/v1/stats", response_model=StatsResponse, tags=["Stats"])
async def get_stats():
    async with async_session() as session:
        users = await UserRepository(session).count()
        images = await ImageRepository(session).total_count()
        revenue = await PaymentRepository(session).total_revenue()
    return StatsResponse(users_total=users, images_total=images, revenue_total=revenue)


@app.post("/api/v1/image/remove-background", response_model=ProcessResponse, tags=["Image"])
async def api_remove_background(file: UploadFile = File(...)):
    """Remove background from uploaded image."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    data = await file.read()
    if len(data) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, "File too large")
    try:
        result, duration = await ImageProcessor.time_it(ImageProcessor.remove_background(data))
        key = await storage.save_bytes(result, folder="api/bg_remove", extension="png")
        return ProcessResponse(success=True, url=f"/files/{key}", duration_ms=duration)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/v1/image/upscale", response_model=ProcessResponse, tags=["Image"])
async def api_upscale(file: UploadFile = File(...), factor: int = 2):
    """Upscale image by factor (2 or 4)."""
    if factor not in (2, 4):
        raise HTTPException(400, "Factor must be 2 or 4")
    data = await file.read()
    try:
        result, duration = await ImageProcessor.time_it(ImageProcessor.upscale(data, factor))
        key = await storage.save_bytes(result, folder="api/upscale", extension="png")
        return ProcessResponse(success=True, url=f"/files/{key}", duration_ms=duration)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/v1/image/enhance", response_model=ProcessResponse, tags=["Image"])
async def api_enhance(file: UploadFile = File(...)):
    """AI enhance uploaded image."""
    data = await file.read()
    try:
        result, duration = await ImageProcessor.time_it(ImageProcessor.enhance(data))
        key = await storage.save_bytes(result, folder="api/enhance", extension="png")
        return ProcessResponse(success=True, url=f"/files/{key}", duration_ms=duration)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/v1/image/passport", response_model=ProcessResponse, tags=["Image"])
async def api_passport(file: UploadFile = File(...)):
    """Generate passport-style photo."""
    data = await file.read()
    try:
        result, duration = await ImageProcessor.time_it(ImageProcessor.passport_photo(data))
        key = await storage.save_bytes(result, folder="api/passport", extension="jpg")
        return ProcessResponse(success=True, url=f"/files/{key}", duration_ms=duration)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/v1/plans", tags=["Plans"])
async def list_plans():
    async with async_session() as session:
        from database.repositories.payment_repo import PlanRepository
        plans = await PlanRepository(session).list_active()
    return [{"id": p.id, "code": p.code, "name": p.name,
             "price": p.price, "currency": p.currency,
             "duration_days": p.duration_days,
             "features": p.features} for p in plans]


@app.get("/files/{path:path}")
async def get_file(path: str):
    try:
        data = await storage.load_bytes(path)
        from fastapi.responses import Response
        return Response(content=data, media_type="image/png")
    except FileNotFoundError:
        raise HTTPException(404, "File not found")