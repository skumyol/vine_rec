"""Decision engine for selecting the best candidate or returning No Image."""

from typing import List, Optional, Tuple
from app.models.candidate import CandidateAnalysis, CandidateScore
from app.models.sku import ParsedSKU
from app.core.config import settings


class DecisionEngine:
    """Makes final decision on candidate selection."""

    def __init__(self):
        self.pass_threshold = settings.PASS_THRESHOLD
        self.review_threshold = settings.REVIEW_THRESHOLD

    def decide(
        self,
        analyses: List[CandidateAnalysis],
        parsed_sku: ParsedSKU
    ) -> Tuple[Optional[CandidateAnalysis], str]:
        """
        Select the best candidate or return None for No Image.

        Returns:
            Tuple of (selected_analysis, reason)
            selected_analysis is None if no suitable candidate found
        """
        if not analyses:
            return None, "No candidates retrieved"

        # Filter to passing candidates only
        passing = [a for a in analyses if a.score.final_verdict == "PASS"]

        if not passing:
            # All candidates failed hard rules
            best_failed = max(analyses, key=lambda a: a.score.total_score)
            return None, self._build_rejection_reason(best_failed)

        # Sort by score descending
        passing.sort(key=lambda a: -a.score.total_score)

        # Check if top candidate meets threshold
        top_candidate = passing[0]

        if top_candidate.score.total_score >= self.pass_threshold:
            return top_candidate, f"Selected with confidence {top_candidate.score.total_score:.1f}"

        if top_candidate.score.total_score >= self.review_threshold:
            return None, f"Top candidate below pass threshold ({top_candidate.score.total_score:.1f}), requires manual review"

        return None, f"No candidate meets quality threshold (best: {top_candidate.score.total_score:.1f})"

    def _build_rejection_reason(self, analysis: CandidateAnalysis) -> str:
        """Build a human-readable rejection reason."""
        reasons = analysis.score.hard_fail_reasons

        if not reasons:
            return f"Failed verification (score: {analysis.score.total_score:.1f})"

        # Map technical reasons to readable text
        reason_map = {
            "multiple_bottles": "multiple bottles in image",
            "lifestyle_image": "lifestyle/prop image",
            "watermark_detected": "watermark detected",
            "too_blurry": "image too blurry",
            "label_not_visible": "label not clearly visible",
            "wrong_producer": "producer mismatch",
            "wrong_appellation": "appellation mismatch",
            "wrong_vineyard": "vineyard/climat mismatch",
            "vintage_mismatch": "vintage mismatch",
        }

        readable = [reason_map.get(r, r) for r in reasons]
        return f"Failed: {', '.join(readable)}"
