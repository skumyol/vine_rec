"""Hard fail rules for rejecting unsafe candidates before scoring."""

from typing import List, Optional
from app.models.candidate import CandidateAnalysis, OpenCVResult, OCRResult
from app.models.sku import ParsedSKU


class HardFailRules:
    """Enforces strict rejection criteria before scoring."""

    # Rejection reasons
    MULTIPLE_BOTTLES = "multiple_bottles"
    LIFESTYLE_IMAGE = "lifestyle_image"
    WATERMARK_DETECTED = "watermark_detected"
    TOO_BLURRY = "too_blurry"
    LABEL_NOT_VISIBLE = "label_not_visible"
    WRONG_PRODUCER = "wrong_producer"
    WRONG_APPELLATION = "wrong_appellation"
    WRONG_VINEYARD = "wrong_vineyard"
    VINTAGE_MISMATCH = "vintage_mismatch"

    def check(
        self,
        analysis: CandidateAnalysis,
        parsed_sku: ParsedSKU
    ) -> List[str]:
        """
        Apply all hard fail rules.

        Returns:
            List of fail reasons (empty if passes)
        """
        fails = []

        # Image quality failures
        fails.extend(self._check_image_quality(analysis))

        # Identity verification failures
        fails.extend(self._check_identity(analysis, parsed_sku))

        return fails

    def _check_image_quality(self, analysis: CandidateAnalysis) -> List[str]:
        """Check image quality criteria."""
        fails = []
        opencv: Optional[OpenCVResult] = analysis.opencv_result

        if not opencv:
            return fails

        if opencv.multiple_bottles:
            fails.append(self.MULTIPLE_BOTTLES)

        if opencv.lifestyle_detected:
            fails.append(self.LIFESTYLE_IMAGE)

        if opencv.watermark_suspected:
            fails.append(self.WATERMARK_DETECTED)

        if not opencv.label_visible:
            fails.append(self.LABEL_NOT_VISIBLE)

        # Sharpness threshold (below 30 is too blurry)
        if opencv.sharpness_score < 30.0:
            fails.append(self.TOO_BLURRY)

        return fails

    def _check_identity(
        self,
        analysis: CandidateAnalysis,
        parsed_sku: ParsedSKU
    ) -> List[str]:
        """Check wine identity criteria."""
        fails = []
        ocr: Optional[OCRResult] = analysis.ocr_result

        if not ocr or not ocr.raw_text:
            return fails

        # Check producer mismatch (producer must be present if parsed)
        if parsed_sku.producer:
            producer_normalized = self._normalize(parsed_sku.producer)
            ocr_text_normalized = self._normalize(ocr.raw_text)

            if producer_normalized not in ocr_text_normalized:
                # Allow for some fuzzy matching via the scorer
                # Only hard fail if obviously wrong producer
                if ocr.producer_found:
                    found_normalized = self._normalize(ocr.producer_found)
                    if not self._is_similar(found_normalized, producer_normalized):
                        fails.append(self.WRONG_PRODUCER)

        # Check appellation mismatch (critical for Burgundy)
        if parsed_sku.appellation:
            appellation_normalized = self._normalize(parsed_sku.appellation)
            ocr_text_normalized = self._normalize(ocr.raw_text)

            # If appellation is clearly different
            if ocr.appellation_found:
                found_normalized = self._normalize(ocr.appellation_found)
                if not self._is_similar(found_normalized, appellation_normalized):
                    fails.append(self.WRONG_APPELLATION)

        # Check vineyard mismatch (critical for Burgundy climats)
        if parsed_sku.vineyard:
            vineyard_normalized = self._normalize(parsed_sku.vineyard)
            ocr_text_normalized = self._normalize(ocr.raw_text)

            # Vineyard must be present if specified in target
            if vineyard_normalized not in ocr_text_normalized:
                if ocr.vineyard_found:
                    found_normalized = self._normalize(ocr.vineyard_found)
                    if not self._is_similar(found_normalized, vineyard_normalized):
                        fails.append(self.WRONG_VINEYARD)
                else:
                    # Missing vineyard where required is a hard fail
                    fails.append(self.WRONG_VINEYARD)

        # Check vintage mismatch if visible
        if parsed_sku.vintage and ocr.vintage_found:
            if ocr.vintage_found != parsed_sku.vintage:
                fails.append(self.VINTAGE_MISMATCH)

        return fails

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        return text.lower().replace("-", " ").replace("'", " ").strip()

    def _is_similar(self, a: str, b: str, threshold: float = 0.7) -> bool:
        """Check if two strings are similar enough."""
        from rapidfuzz import fuzz
        ratio = fuzz.ratio(a, b) / 100.0
        return ratio >= threshold
