from typing import Dict, Any, List, Tuple, Optional
from rapidfuzz import fuzz, process

from app.models.sku import ParsedSKU
from app.models.candidate import OCRResult
from app.core.constants import FIELD_MATCH_WEIGHTS, SYNONYM_MAPPINGS


# Generic French / wine-trade words that often appear in SKU names but
# rarely on the bottle label itself (or appear inconsistently).
# Filtering these prevents false producer_mismatch / appellation_mismatch.
_STOP_WORDS = {
    "domaine", "chateau", "château", "ch", "ch.",
    "le", "la", "les", "l",
    "de", "du", "des", "d", "of",
    "the", "and", "et",
    "vin", "wine", "wines", "winery",
    "cuvee", "cuvée",
    "estate", "vineyard", "vineyards",
}


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
        threshold: int = 70,
        min_match_ratio: float = 0.5,
    ) -> Tuple[float, bool]:
        """Match a target field against OCR text.

        Strategy:
        - Strip generic stop-words ("domaine", "chateau", "le", ...) from target,
          since they often don't appear on the actual label.
        - For each significant target token, score with `partial_ratio` against
          the entire OCR text (handles substring + multi-word labels well) and
          also try the bare token-in-text fast path.
        - Field is a "match" when at least `min_match_ratio` of the significant
          tokens score above `threshold`. Score returned is the average.
        """
        if not target:
            return 100.0, True

        ocr_text_lc = ocr_text.lower()
        if not ocr_text_lc.strip():
            return 0.0, False

        # Tokenize + drop stop-words and very short tokens
        raw_tokens = target.lower().replace("-", " ").split()
        significant = [
            t for t in raw_tokens
            if t not in _STOP_WORDS and len(t) > 2
        ]

        # If everything was a stop-word (e.g. target was just "Domaine"),
        # fall back to whole-string fuzzy match.
        if not significant:
            score = fuzz.partial_ratio(target.lower(), ocr_text_lc)
            return float(score), score >= threshold

        scores: List[float] = []
        matched = 0

        for token in significant:
            # Fast path: literal substring
            if token in ocr_text_lc:
                scores.append(100.0)
                matched += 1
                continue

            # Fuzzy partial match against the whole OCR text
            score = fuzz.partial_ratio(token, ocr_text_lc)
            if score >= threshold:
                scores.append(float(score))
                matched += 1
                continue

            # Synonym fallback (e.g. "saint" <-> "st")
            best_syn = score
            for syn in self._get_synonyms(token):
                if syn in ocr_text_lc:
                    best_syn = max(best_syn, 100.0)
                    break
                s = fuzz.partial_ratio(syn, ocr_text_lc)
                if s > best_syn:
                    best_syn = s

            scores.append(float(best_syn))
            if best_syn >= threshold:
                matched += 1

        match_ratio = matched / len(significant)
        avg_score = sum(scores) / len(scores)
        return avg_score, match_ratio >= min_match_ratio
    
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
