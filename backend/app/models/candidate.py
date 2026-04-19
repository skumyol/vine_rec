from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ImageCandidate(BaseModel):
    id: Optional[str] = None
    source_query: str
    source_page: Optional[str] = None
    source_domain: Optional[str] = None
    image_url: str
    local_path: Optional[str] = None
    original_path: Optional[str] = None
    
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    perceptual_hash: Optional[str] = None
    
    source_trust_score: int = 1
    download_status: str = "pending"
    download_error: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OpenCVResult(BaseModel):
    single_bottle: bool = False
    upright: bool = False
    background_clean: bool = False
    sharpness_score: float = 0.0
    glare_score: float = 0.0
    label_visible: bool = False
    watermark_suspected: bool = False
    multiple_bottles: bool = False
    lifestyle_detected: bool = False
    opencv_pass: bool = False
    rejection_reason: Optional[str] = None


class OCRResult(BaseModel):
    raw_text: str = ""
    normalized_text: str = ""
    tokens: List[str] = []
    producer_found: Optional[str] = None
    appellation_found: Optional[str] = None
    vintage_found: Optional[str] = None
    confidence: float = 0.0


class VLMVerification(BaseModel):
    is_real_photo: bool = False
    single_bottle: bool = False
    background_ok: bool = False
    producer_match: bool = False
    appellation_match: bool = False
    vineyard_match: bool = False
    vintage_match: bool = False
    classification_match: bool = False
    reasoning_summary: str = ""
    confidence: float = 0.0
    raw_response: Optional[str] = None


class CandidateScore(BaseModel):
    image_quality_score: float = 0.0
    text_verification_score: float = 0.0
    vlm_verification_score: float = 0.0
    total_score: float = 0.0
    field_matches: Dict[str, bool] = {}
    hard_fail_reasons: List[str] = []
    final_verdict: str = "FAIL"


class CandidateAnalysis(BaseModel):
    candidate_id: str
    run_id: str
    
    opencv_result: Optional[OpenCVResult] = None
    ocr_result: Optional[OCRResult] = None
    gemini_result: Optional[VLMVerification] = None
    qwen_result: Optional[VLMVerification] = None
    
    score: CandidateScore
    
    label_crop_path: Optional[str] = None
    bottle_crop_path: Optional[str] = None
    neck_crop_path: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
