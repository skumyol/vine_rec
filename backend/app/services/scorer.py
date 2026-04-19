from typing import Dict, Any, List, Optional, Tuple

from app.models.candidate import (
    OpenCVResult, OCRResult, VLMVerification, 
    CandidateScore, CandidateAnalysis
)
from app.core.constants import SCORE_WEIGHTS, Verdict


class ScoringEngine:
    def __init__(self):
        self.pass_threshold = 25  # Lowered from 30
        self.review_threshold = 15  # Lowered from 20
    
    def score(
        self,
        opencv_result: Optional[OpenCVResult],
        ocr_result: Optional[OCRResult],
        gemini_result: Optional[VLMVerification],
        qwen_result: Optional[VLMVerification],
        text_verification_score: float,
        field_matches: Dict[str, bool],
        hard_fails: List[str]
    ) -> CandidateScore:
        
        image_quality_score = self._score_image_quality(opencv_result)
        
        vlm_score = self._score_vlm_verification(gemini_result, qwen_result)
        
        text_score = text_verification_score
        
        total_score = (
            image_quality_score * SCORE_WEIGHTS["image_quality"] / 100 +
            text_score * SCORE_WEIGHTS["text_verification"] / 100 +
            vlm_score * SCORE_WEIGHTS["vlm_verification"] / 100
        )
        
        final_verdict = self._determine_verdict(
            total_score, hard_fails, opencv_result, 
            gemini_result, qwen_result
        )
        
        return CandidateScore(
            image_quality_score=image_quality_score,
            text_verification_score=text_score,
            vlm_verification_score=vlm_score,
            total_score=total_score,
            field_matches=field_matches,
            hard_fail_reasons=hard_fails,
            final_verdict=final_verdict
        )
    
    def _score_image_quality(self, opencv_result: Optional[OpenCVResult]) -> float:
        if not opencv_result:
            return 0.0
        
        # Start with reduced score if opencv_pass failed, but don't zero out completely
        score = 100.0 if opencv_result.opencv_pass else 50.0
        
        if opencv_result.sharpness_score < 0.5:
            score -= 20
        if opencv_result.sharpness_score < 0.3:
            score -= 30
        
        if opencv_result.glare_score > 0.3:
            score -= 15
        if opencv_result.glare_score > 0.5:
            score -= 30
        
        if not opencv_result.background_clean:
            score -= 20
        
        if not opencv_result.label_visible:
            score -= 25
        
        return max(0.0, score)
    
    def _score_vlm_verification(
        self,
        gemini_result: Optional[VLMVerification],
        qwen_result: Optional[VLMVerification]
    ) -> float:
        scores = []
        
        if gemini_result:
            gemini_score = self._calculate_vlm_score(gemini_result)
            scores.append(gemini_score)
        
        if qwen_result:
            qwen_score = self._calculate_vlm_score(qwen_result)
            scores.append(qwen_score)
        
        if not scores:
            return 0.0
        
        if len(scores) == 2:
            avg = sum(scores) / 2
            
            gemini_conf = gemini_result.confidence if gemini_result else 0
            qwen_conf = qwen_result.confidence if qwen_result else 0
            
            if abs(gemini_conf - qwen_conf) > 0.3:
                avg *= 0.9
            
            if gemini_result and qwen_result:
                matches = sum([
                    gemini_result.producer_match == qwen_result.producer_match,
                    gemini_result.appellation_match == qwen_result.appellation_match,
                    gemini_result.vintage_match == qwen_result.vintage_match
                ])
                if matches < 2:
                    avg *= 0.85
            
            return avg
        
        return scores[0]
    
    def _calculate_vlm_score(self, result: VLMVerification) -> float:
        if not result.is_real_photo:
            return 0.0
        
        score = 100.0
        
        if not result.single_bottle:
            score -= 40
        if not result.background_ok:
            score -= 30
        
        match_scores = [
            result.producer_match,
            result.appellation_match,
            result.vineyard_match,
            result.vintage_match,
            result.classification_match
        ]
        
        true_matches = sum(1 for m in match_scores if m)
        total_fields = len([m for m in match_scores if m is not None])
        
        if total_fields > 0:
            match_ratio = true_matches / total_fields
            score *= match_ratio
        
        score *= (0.5 + 0.5 * result.confidence)
        
        return max(0.0, min(100.0, score))
    
    def _determine_verdict(
        self,
        total_score: float,
        hard_fails: List[str],
        opencv_result: Optional[OpenCVResult],
        gemini_result: Optional[VLMVerification],
        qwen_result: Optional[VLMVerification]
    ) -> str:
        if hard_fails:
            # Only producer, appellation, vineyard are critical - vintage can be hard to read
            critical_fails = [
                "producer_mismatch",
                "appellation_mismatch",
                "vineyard_mismatch"
            ]
            if any(f in critical_fails for f in hard_fails):
                return Verdict.FAIL
        
        # Relaxed - opencv warnings don't cause hard fail, just affect score
        # if opencv_result and not opencv_result.opencv_pass:
        #     return Verdict.FAIL
        
        # Relaxed - VLM is_real_photo warnings don't cause hard fail
        # if gemini_result and qwen_result:
        #     if not gemini_result.is_real_photo or not qwen_result.is_real_photo:
        #         return Verdict.FAIL
        # elif gemini_result:
        #     if not gemini_result.is_real_photo:
        #         return Verdict.FAIL
        # elif qwen_result:
        #     if not qwen_result.is_real_photo:
        #         return Verdict.FAIL
        
        if total_score >= self.pass_threshold:
            return Verdict.PASS
        elif total_score >= self.review_threshold:
            return Verdict.REVIEW
        else:
            return Verdict.FAIL
    
    def select_best_candidate(
        self,
        analyses: List[CandidateAnalysis]
    ) -> Tuple[Optional[CandidateAnalysis], str]:
        if not analyses:
            return None, "No candidates to evaluate"
        
        passing = [
            a for a in analyses 
            if a.score.final_verdict == Verdict.PASS
        ]
        
        if passing:
            best = max(passing, key=lambda a: a.score.total_score)
            return best, f"Selected best passing candidate with score {best.score.total_score:.1f}"
        
        review = [
            a for a in analyses
            if a.score.final_verdict == Verdict.REVIEW
        ]
        
        if review:
            best = max(review, key=lambda a: a.score.total_score)
            return best, f"No passing candidates. Best review candidate score: {best.score.total_score:.1f}"
        
        best = max(analyses, key=lambda a: a.score.total_score)
        return None, f"No acceptable candidates. Highest score was {best.score.total_score:.1f}"
