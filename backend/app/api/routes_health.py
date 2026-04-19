from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.gemini_verifier import GeminiVerifier
from app.services.qwen_verifier import QwenVerifier
from app.services.search_service import SearchService

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    services: Dict[str, Any]
    config: Dict[str, Any]


class AnalyzerModesResponse(BaseModel):
    modes: list[str]
    default: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health and service availability."""
    
    gemini = GeminiVerifier()
    qwen = QwenVerifier()
    
    services = {
        "gemini": {
            "available": gemini.is_available(),
            "model": settings.GEMINI_MODEL if gemini.is_available() else None
        },
        "qwen": {
            "available": qwen.is_available(),
            "model": qwen.model_name if qwen.is_available() else None,
            "provider": "openrouter" if (qwen.is_available() and qwen.use_openrouter) else "native"
        },
        "search": {
            "provider": settings.SEARCH_PROVIDER,
            "configured": settings.SEARCH_API_KEY is not None
        },
        "ocr": {
            "engine": settings.OCR_ENGINE
        }
    }
    
    all_services_ok = all([
        services["gemini"]["available"] or services["qwen"]["available"],
        services["search"]["configured"]
    ])
    
    return HealthResponse(
        status="healthy" if all_services_ok else "degraded",
        services=services,
        config={
            "default_analyzer_mode": settings.DEFAULT_ANALYZER_MODE,
            "pass_threshold": settings.PASS_THRESHOLD,
            "review_threshold": settings.REVIEW_THRESHOLD
        }
    )


@router.get("/analyzer-modes", response_model=AnalyzerModesResponse)
async def get_analyzer_modes():
    """Get available analyzer modes."""
    from app.core.constants import AnalyzerMode
    
    return AnalyzerModesResponse(
        modes=[
            AnalyzerMode.OPENCV_ONLY,
            AnalyzerMode.GEMINI,
            AnalyzerMode.QWEN_VL,
            AnalyzerMode.HYBRID_FAST,
            AnalyzerMode.HYBRID_STRICT
        ],
        default=settings.DEFAULT_ANALYZER_MODE
    )
