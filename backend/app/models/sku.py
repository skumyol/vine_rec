from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class WineSKUInput(BaseModel):
    wine_name: str = Field(..., description="Full wine name")
    vintage: Optional[str] = Field(None, description="Vintage year")
    format: Optional[str] = Field(None, description="Bottle format (e.g., 750ml)")
    region: Optional[str] = Field(None, description="Wine region")
    
    class Config:
        json_schema_extra = {
            "example": {
                "wine_name": "Domaine Rossignol-Trapet Latricieres-Chambertin Grand Cru",
                "vintage": "2017",
                "format": "750ml",
                "region": "Burgundy"
            }
        }


class ParsedSKU(BaseModel):
    raw_name: str
    producer: Optional[str] = None
    producer_normalized: Optional[str] = None
    appellation: Optional[str] = None
    appellation_normalized: Optional[str] = None
    vineyard: Optional[str] = None
    vineyard_normalized: Optional[str] = None
    classification: Optional[str] = None
    classification_normalized: Optional[str] = None
    cuvee: Optional[str] = None
    cuvee_normalized: Optional[str] = None
    vintage: Optional[str] = None
    format_ml: Optional[int] = None
    region: Optional[str] = None
    normalized_tokens: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "producer": self.producer,
            "appellation": self.appellation,
            "vineyard": self.vineyard,
            "classification": self.classification,
            "vintage": self.vintage,
        }


class SearchQuery(BaseModel):
    query: str
    query_type: str  # exact, relaxed, vintage_fallback
    priority: int


class AnalysisRequest(BaseModel):
    wine_name: str
    vintage: Optional[str] = None
    format: Optional[str] = None
    region: Optional[str] = None
    analyzer_mode: str = "hybrid_fast"
    
    class Config:
        json_schema_extra = {
            "example": {
                "wine_name": "Domaine Arlaud Morey-St-Denis Monts Luisants 1er Cru",
                "vintage": "2019",
                "format": "750ml",
                "region": "Burgundy",
                "analyzer_mode": "hybrid_strict"
            }
        }


class BatchAnalysisRequest(BaseModel):
    wines: List[WineSKUInput]
    analyzer_mode: str = "hybrid_fast"


class AnalysisResult(BaseModel):
    input: WineSKUInput
    parsed_sku: ParsedSKU
    selected_image_url: Optional[str] = None
    confidence: float = 0.0
    verdict: str = "FAIL"
    reason: str = ""
    analyzer_mode: str = ""
    top_candidates: List[Dict[str, Any]] = []
    processing_time_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
