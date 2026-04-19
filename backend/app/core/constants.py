from enum import Enum


class AnalyzerMode(str, Enum):
    OPENCV_ONLY = "opencv_only"
    GEMINI = "gemini"
    QWEN_VL = "qwen_vl"
    HYBRID_FAST = "hybrid_fast"
    HYBRID_STRICT = "hybrid_strict"


class Verdict(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"
    NO_IMAGE = "NO_IMAGE"


class HardFailReason(str, Enum):
    PRODUCER_MISMATCH = "producer_mismatch"
    APPELLATION_MISMATCH = "appellation_mismatch"
    VINEYARD_MISMATCH = "vineyard_mismatch"
    VINTAGE_MISMATCH = "vintage_mismatch"
    MULTIPLE_BOTTLES = "multiple_bottles"
    LIFESTYLE_IMAGE = "lifestyle_image"
    WATERMARK_DETECTED = "watermark_detected"
    SEVERE_BLUR = "severe_blur"
    UNREADABLE_LABEL = "unreadable_label"
    AI_GENERATED = "ai_generated"


SCORE_WEIGHTS = {
    "image_quality": 20,
    "text_verification": 40,
    "vlm_verification": 40,
}

FIELD_MATCH_WEIGHTS = {
    "producer": 30,
    "appellation": 30,
    "vineyard": 20,
    "vintage": 10,
    "classification": 10,
}

SOURCE_TRUST_RANKING = {
    "winery": 5,
    "merchant": 4,
    "distributor": 4,
    "review_site": 3,
    "auction": 3,
    "blog": 1,
    "unknown": 1,
}

SYNONYM_MAPPINGS = {
    "st": ["saint", "st"],
    "saint": ["saint", "st"],
    "ste": ["sainte", "ste"],
    "sainte": ["sainte", "ste"],
    "mont": ["mont", "mount"],
    "mount": ["mont", "mount"],
    "clos": ["clos"],
    "chateau": ["chateau", "château"],
    "château": ["chateau", "château"],
    "domaine": ["domaine"],
    "grand cru": ["grand cru", "grand-cru"],
    "premier cru": ["premier cru", "premier-cru", "1er cru", "1er-cru"],
    "1er cru": ["premier cru", "premier-cru", "1er cru", "1er-cru"],
}

BURGUNDY_GRAND_CRUS = [
    "chambertin", "chambertin-clos de beze", "chapelle-chambertin",
    "charmes-chambertin", "griotte-chambertin", "latricieres-chambertin",
    "mazis-chambertin", "mazoyeres-chambertin", "ruchottes-chambertin",
    "bonnes-mares", "clos de la roche", "clos des lambrays",
    "clos de tart", "clos de vougeot", "echzeaux", "grand echezeaux",
    "la grande rue", "la tache", "richebourg", "romanee-conti",
    "romanee-saint-vivant", "romanee-st-vivant", "la romanee",
]
