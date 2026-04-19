from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from dotenv import load_dotenv

# Force reload of .env file
load_dotenv('/Users/skumyol/Documents/GitHub/vine_rec/.env', override=True)


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    API_BASE_URL: str = "http://localhost:8001"
    FRONTEND_URL: str = "http://localhost:3001"
    
    SEARCH_PROVIDER: str = "auto"
    SEARCH_API_KEY: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None
    
    GEMINI_API_KEY: Optional[str] = None
    QWEN_API_KEY: Optional[str] = None
    QWEN_BASE_URL: Optional[str] = None
    
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "qwen/qwen-2.5-vl-7b-instruct"
    
    OCR_ENGINE: str = "easyocr"
    
    DB_URL: str = "sqlite:///data/app.db"
    
    IMAGE_STORAGE: str = "data/images"
    CACHE_DIR: str = "data/cache"
    RESULT_DIR: str = "data/results"
    
    DEFAULT_ANALYZER_MODE: str = "hybrid_fast"
    PASS_THRESHOLD: int = 35
    REVIEW_THRESHOLD: int = 25

    VINOBUZZ_SESSION_ID: Optional[str] = None
    
    MAX_CANDIDATES_PER_QUERY: int = 10
    MAX_QUERIES_PER_SKU: int = 6
    # Hard cap on candidates that flow into OCR/VLM (dominant cost)
    MAX_TOTAL_CANDIDATES: int = 6
    # Parallelism for candidate analysis (OCR+VLM) per SKU
    ANALYSIS_CONCURRENCY: int = 3
    
    OPENCV_MIN_DIMENSION: int = 400
    OPENCV_MAX_DIMENSION: int = 4000
    OPENCV_MIN_SHARPNESS: float = 50.0
    
    GEMINI_MODEL: str = "gemini-1.5-flash"
    QWEN_MODEL: str = "qwen-vl-max"
    
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://skumyol.com"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
