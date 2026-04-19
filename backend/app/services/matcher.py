from typing import Dict, Any, List, Tuple, Optional
from rapidfuzz import fuzz, process

from app.models.sku import ParsedSKU
from app.models.candidate import OCRResult
from app.core.constants import FIELD_MATCH_WEIGHTS, SYNONYM_MAPPINGS


class TextMatcher:
    def __init__(self):
        self.weights = FIELD_MATCH_WEIGHTS
    
    def match(
        self,
        parsed_sku: ParsedSKU,
        ocr_result: OCRResult
    ) -> Tuple[float, Dict[str, bool], List[str]]:
        field_matches = {}
        hard_fails = []
        
        producer_score, producer_match = self._match_field(
            parsed_sku.producer_normalized,
            ocr_result.normalized_text,
            threshold=70
        )
        field_matches["producer"] = producer_match
        if parsed_sku.producer and not producer_match:
            hard_fails.append("producer_mismatch")
        
        appellation_score, appellation_match = self._match_field(
            parsed_sku.appellation_normalized,
            ocr_result.normalized_text,
            threshold=65
        )
        field_matches["appellation"] = appellation_match
        if parsed_sku.appellation and not appellation_match:
            hard_fails.append("appellation_mismatch")
        
        vineyard_score, vineyard_match = self._match_field(
            parsed_sku.vineyard_normalized,
            ocr_result.normalized_text,
            threshold=60
        )
        field_matches["vineyard"] = vineyard_match
        if parsed_sku.vineyard and not vineyard_match:
            if vineyard_score < 40:
                hard_fails.append("vineyard_mismatch")
        
        vintage_score, vintage_match = self._match_vintage(
            parsed_sku.vintage,
            ocr_result.vintage_found
        )
        field_matches["vintage"] = vintage_match
        if parsed_sku.vintage and ocr_result.vintage_found:
            if not vintage_match:
                hard_fails.append("vintage_mismatch")
        
        classification_score, classification_match = self._match_field(
            parsed_sku.classification_normalized,
            ocr_result.normalized_text,
            threshold=60
        )
        field_matches["classification"] = classification_match
        
        total_score = (
            producer_score * self.weights["producer"] / 100 +
            appellation_score * self.weights["appellation"] / 100 +
            vineyard_score * self.weights["vineyard"] / 100 +
            vintage_score * self.weights["vintage"] / 100 +
            classification_score * self.weights["classification"] / 100
        )
        
        return total_score, field_matches, hard_fails
    
    def _match_field(
        self,
        target: Optional[str],
        ocr_text: str,
        threshold: int = 60
    ) -> Tuple[float, bool]:
        if not target:
            return 100.0, True
        
        ocr_tokens = ocr_text.split()
        target_tokens = target.split()
        
        for target_token in target_tokens:
            if len(target_token) <= 2:
                continue
            
            if target_token in ocr_tokens:
                continue
            
            matches = process.extract(target_token, ocr_tokens, scorer=fuzz.ratio, limit=3)
            if matches and matches[0][1] >= threshold:
                continue
            
            synonyms = self._get_synonyms(target_token)
            synonym_matched = False
            for syn in synonyms:
                if syn in ocr_tokens:
                    synonym_matched = True
                    break
                matches = process.extract(syn, ocr_tokens, scorer=fuzz.ratio, limit=1)
                if matches and matches[0][1] >= threshold:
                    synonym_matched = True
                    break
            
            if not synonym_matched:
                score = max([m[1] for m in matches]) if matches else 0
                return score, False
        
        return 100.0, True
    
    def _match_vintage(
        self,
        target_vintage: Optional[str],
        ocr_vintage: Optional[str]
    ) -> Tuple[float, bool]:
        if not target_vintage:
            return 100.0, True
        
        if not ocr_vintage:
            # Vintage not detected by OCR - don't penalize, labels can be hard to read
            return 85.0, True
        
        if target_vintage == ocr_vintage:
            return 100.0, True
        
        try:
            target_year = int(target_vintage)
            ocr_year = int(ocr_vintage)
            diff = abs(target_year - ocr_year)
            if diff == 0:
                return 100.0, True
            elif diff == 1:
                # One year difference - could be misread, not a hard fail
                return 75.0, True
            else:
                # Different vintage - significant mismatch
                return 30.0, False
        except:
            return 50.0, True
    
    def _get_synonyms(self, token: str) -> List[str]:
        token_lower = token.lower()
        if token_lower in SYNONYM_MAPPINGS:
            return SYNONYM_MAPPINGS[token_lower]
        return []
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        return fuzz.token_set_ratio(text1.lower(), text2.lower())
