from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import routes_analyze, routes_health, routes_wines, routes_results, routes_jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    os.makedirs(settings.IMAGE_STORAGE, exist_ok=True)
    os.makedirs(settings.CACHE_DIR, exist_ok=True)
    os.makedirs(settings.RESULT_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.IMAGE_STORAGE, "original"), exist_ok=True)
    os.makedirs(os.path.join(settings.IMAGE_STORAGE, "processed"), exist_ok=True)
    os.makedirs(os.path.join(settings.IMAGE_STORAGE, "crops"), exist_ok=True)

    # Warm heavy resources so the first SKU doesn't pay the cold-start cost
    import asyncio as _asyncio
    try:
        from app.services.ocr_service import _get_shared_reader
        print("Warming EasyOCR reader...")
        await _asyncio.to_thread(_get_shared_reader)
        print("EasyOCR reader ready")
    except Exception as e:
        print(f"OCR warmup skipped: {e}")

    yield

    print("Shutting down...")
    try:
        from app.services.browser_manager import BrowserManager
        if BrowserManager._instance is not None:
            await BrowserManager._instance.shutdown()
    except Exception as e:
        print(f"Browser shutdown error: {e}")


app = FastAPI(
    title="Wine Photo Verification API",
    description="API for verifying wine bottle images using OpenCV, OCR, and VLM analysis",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_analyze.router, prefix="/api")
app.include_router(routes_health.router, prefix="/api")
app.include_router(routes_wines.router, prefix="/api")
app.include_router(routes_results.router, prefix="/api")
app.include_router(routes_jobs.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Wine Photo Verification API",
        "docs": "/api/docs",
        "health": "/api/health"
    }


@app.get("/api/docs")
async def docs_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")
