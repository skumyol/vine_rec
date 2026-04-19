"""Result models for API responses."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.sku import WineSKUInput, ParsedSKU
from app.models.candidate import CandidateAnalysis


class FieldMatchRow(BaseModel):
    """Single field comparison row."""
    field_name: str
    target_value: Optional[str]
    extracted_value: Optional[str]
    matched: bool
    confidence: float
    evidence: Optional[str] = None


class RunResult(BaseModel):
    """Full run result with all details."""
    run_id: str
    input: WineSKUInput
    parsed_sku: ParsedSKU
    
    # Final outcome
    verdict: str = "FAIL"
    confidence: float = 0.0
    selected_image_url: Optional[str] = None
    selected_candidate_id: Optional[str] = None
    reason: str = ""
    
    # Processing metadata
    analyzer_mode: str = "hybrid_fast"
    processing_time_ms: Optional[int] = None
    
    # All candidates analyzed
    candidates: List[CandidateAnalysis] = []
    
    # Field-level matches for selected candidate
    field_matches: List[FieldMatchRow] = []
    
    # Stage timings
    retrieval_time_ms: Optional[int] = None
    download_time_ms: Optional[int] = None
    ocr_time_ms: Optional[int] = None
    scoring_time_ms: Optional[int] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BatchRunSummary(BaseModel):
    """Summary of a batch run."""
    batch_id: str
    total_wines: int
    passed: int
    failed: int
    no_image: int
    processing_time_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BatchRunDetail(BaseModel):
    """Full batch run with all results."""
    summary: BatchRunSummary
    results: List[RunResult]
