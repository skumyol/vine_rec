import asyncio
import os
import time
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid

from app.models.sku import WineSKUInput, ParsedSKU, AnalysisRequest, AnalysisResult
from app.models.candidate import ImageCandidate, CandidateAnalysis, CandidateScore
from app.services.parser import WineParser, QueryBuilder
from app.services.search_service import SearchService
from app.services.downloader import ImageDownloader
from app.services.image_preprocess import ImagePreprocessor
from app.services.opencv_filter import OpenCVFilter
from app.services.label_cropper import LabelCropper
from app.services.ocr_service import OCRService
from app.services.matcher import TextMatcher
from app.services.gemini_verifier import GeminiVerifier
from app.services.qwen_verifier import QwenVerifier
from app.services.scorer import ScoringEngine
from app.core.constants import AnalyzerMode, Verdict
from app.core.config import settings
from app.core.timing import PipelineTimer


class AnalysisPipeline:
    def __init__(self):
        self.parser = WineParser()
        self.query_builder = QueryBuilder()
        self.search_service = SearchService()
        self.downloader = ImageDownloader()
        self.preprocessor = ImagePreprocessor()
        self.opencv_filter = OpenCVFilter()
        self.label_cropper = LabelCropper()
        self.ocr_service = OCRService()
        self.matcher = TextMatcher()
        self.gemini_verifier = GeminiVerifier()
        self.qwen_verifier = QwenVerifier()
        self.scorer = ScoringEngine()
    
    async def analyze(
        self,
        request: AnalysisRequest
    ) -> AnalysisResult:
        timer = PipelineTimer()
        run_id = str(uuid.uuid4())[:8]
        total_start = time.perf_counter()
        print(f"[{run_id}] Starting analysis for: {request.wine_name}")
        
        wine_input = WineSKUInput(
            wine_name=request.wine_name,
            vintage=request.vintage,
            format=request.format,
            region=request.region
        )
        
        parsed_sku = self.parser.parse(wine_input)
        print(f"[{run_id}] Parsed: {parsed_sku.producer} | {parsed_sku.appellation} | {parsed_sku.vineyard}")
        
        queries = self.query_builder.build_queries(parsed_sku)
        print(f"[{run_id}] Generated {len(queries)} search queries")
        
        with timer.stage("retrieval"):
            candidates = await self.search_service.search_candidates(parsed_sku, queries)
        print(f"[{run_id}] Found {len(candidates)} unique candidates ({timer.timing.retrieval_ms}ms)")
        
        with timer.stage("download"):
            downloaded = await self._download_candidates(candidates)
        print(f"[{run_id}] Downloaded {len([c for c in downloaded if c.download_status == 'downloaded'])} new images, {len([c for c in downloaded if c.download_status == 'cached'])} cached ({timer.timing.download_ms}ms)")
        
        with timer.stage("analysis"):
            analyses = await self._analyze_candidates(
                downloaded, parsed_sku, request.analyzer_mode, timer
            )
        print(f"[{run_id}] Completed analysis on {len(analyses)} candidates")
        
        best_candidate, selection_reason = self.scorer.select_best_candidate(analyses)
        
        total_ms = int((time.perf_counter() - total_start) * 1000)
        timer.set_total(total_ms)
        
        if best_candidate and best_candidate.score.final_verdict in (Verdict.PASS, Verdict.REVIEW):
            candidate_obj = next(
                (c for c in downloaded if c.id == best_candidate.candidate_id),
                None
            )
            
            result = AnalysisResult(
                input=wine_input,
                parsed_sku=parsed_sku,
                selected_image_url=candidate_obj.image_url if candidate_obj else None,
                confidence=best_candidate.score.total_score,
                verdict=best_candidate.score.final_verdict,
                reason=self._build_reason(best_candidate, selection_reason),
                analyzer_mode=request.analyzer_mode,
                top_candidates=self._format_top_candidates(analyses, downloaded),
                processing_time_ms=total_ms
            )
        else:
            # Report best score even when nothing acceptable was found
            top_score = 0.0
            if analyses:
                top_score = max(a.score.total_score for a in analyses)
            
            result = AnalysisResult(
                input=wine_input,
                parsed_sku=parsed_sku,
                selected_image_url=None,
                confidence=top_score,
                verdict=Verdict.NO_IMAGE,
                reason=selection_reason,
                analyzer_mode=request.analyzer_mode,
                top_candidates=self._format_top_candidates(analyses, downloaded),
                processing_time_ms=total_ms
            )
        
        print(f"[{run_id}] Result: {result.verdict} | Confidence: {result.confidence:.1f} | Total: {timer.timing.total_ms}ms")
        return result
    
    async def _download_candidates(
        self,
        candidates: List[ImageCandidate]
    ) -> List[ImageCandidate]:
        tasks = [self.downloader.download(c) for c in candidates]
        downloaded = await asyncio.gather(*tasks)
        
        successful = [d for d in downloaded if d.download_status in ("downloaded", "cached")]
        
        preprocessed = []
        for candidate in successful:
            preprocessed.append(self.preprocessor.preprocess(candidate))
        
        return preprocessed
    
    async def _analyze_candidates(
        self,
        candidates: List[ImageCandidate],
        parsed_sku: ParsedSKU,
        analyzer_mode: str,
        timer: PipelineTimer
    ) -> List[CandidateAnalysis]:
        """Analyze candidates in parallel batches with short-circuit on PASS.

        OCR is CPU-bound (run in a thread via run_in_executor inside the
        single-candidate helper), VLM is I/O-bound. Running multiple candidates
        concurrently overlaps both. We also short-circuit as soon as a batch
        produces a PASS candidate to skip the rest.
        """
        usable = [
            c for c in candidates
            if c.download_status in ("downloaded", "cached")
        ]
        if not usable:
            return []

        concurrency = max(1, settings.ANALYSIS_CONCURRENCY)
        analyses: List[CandidateAnalysis] = []

        for i in range(0, len(usable), concurrency):
            batch = usable[i:i + concurrency]
            batch_results = await asyncio.gather(
                *[
                    self._analyze_single_candidate(c, parsed_sku, analyzer_mode)
                    for c in batch
                ],
                return_exceptions=True,
            )
            for r in batch_results:
                if isinstance(r, Exception):
                    print(f"Candidate analysis error: {r}")
                    continue
                analyses.append(r)

            # Short-circuit: if any candidate in this batch already passes,
            # stop burning OCR/VLM cycles on the rest.
            if any(a.score.final_verdict == Verdict.PASS for a in analyses):
                break

        return analyses
    
    async def _analyze_single_candidate(
        self,
        candidate: ImageCandidate,
        parsed_sku: ParsedSKU,
        analyzer_mode: str
    ) -> CandidateAnalysis:
        run_id = str(uuid.uuid4())[:6]

        # Sync CPU-bound steps (OpenCV + crop + OCR) are offloaded to a thread
        # so concurrent candidates can truly overlap and VLM calls aren't blocked.
        def _sync_stage():
            ocv = self.opencv_filter.analyze(candidate)
            bbox = self.opencv_filter.get_bottle_bbox(candidate)
            c = self.label_cropper.extract_crops(candidate, bbox)
            ocr = self.ocr_service.extract_text(candidate, c)
            return ocv, c, ocr

        opencv_result, crops, ocr_result = await asyncio.to_thread(_sync_stage)

        text_score, field_matches, hard_fails = self.matcher.match(parsed_sku, ocr_result)
        
        gemini_result = None
        qwen_result = None

        use_gemini = (
            analyzer_mode in (AnalyzerMode.GEMINI, AnalyzerMode.HYBRID_FAST, AnalyzerMode.HYBRID_STRICT)
            and self.gemini_verifier.is_available()
        )
        use_qwen = (
            analyzer_mode in (AnalyzerMode.QWEN_VL, AnalyzerMode.HYBRID_STRICT)
            and self.qwen_verifier.is_available()
        )

        # Run VLM verifiers in parallel when both are active
        tasks = []
        if use_gemini:
            tasks.append(self.gemini_verifier.verify(candidate.local_path, parsed_sku, ocr_result.raw_text))
        else:
            tasks.append(asyncio.sleep(0, result=None))
        if use_qwen:
            tasks.append(self.qwen_verifier.verify(candidate.local_path, parsed_sku, ocr_result.raw_text))
        else:
            tasks.append(asyncio.sleep(0, result=None))

        gemini_result, qwen_result = await asyncio.gather(*tasks, return_exceptions=False)
        
        score = self.scorer.score(
            opencv_result=opencv_result,
            ocr_result=ocr_result,
            gemini_result=gemini_result,
            qwen_result=qwen_result,
            text_verification_score=text_score,
            field_matches=field_matches,
            hard_fails=hard_fails
        )
        
        return CandidateAnalysis(
            candidate_id=candidate.id,
            run_id=run_id,
            opencv_result=opencv_result,
            ocr_result=ocr_result,
            gemini_result=gemini_result,
            qwen_result=qwen_result,
            score=score,
            label_crop_path=crops.get("label"),
            bottle_crop_path=crops.get("full"),
            neck_crop_path=crops.get("neck")
        )
    
    def _build_reason(self, analysis: CandidateAnalysis, selection_reason: str) -> str:
        parts = [selection_reason]
        
        if analysis.gemini_result:
            parts.append(f"Gemini: {analysis.gemini_result.reasoning_summary[:100]}")
        
        if analysis.ocr_result:
            fields = []
            if analysis.score.field_matches.get("producer"):
                fields.append("producer")
            if analysis.score.field_matches.get("appellation"):
                fields.append("appellation")
            if analysis.score.field_matches.get("vineyard"):
                fields.append("vineyard")
            if analysis.score.field_matches.get("vintage"):
                fields.append("vintage")
            
            if fields:
                parts.append(f"Matched fields: {', '.join(fields)}")
        
        return "; ".join(parts)
    
    def _format_top_candidates(
        self,
        analyses: List[CandidateAnalysis],
        candidates: List[ImageCandidate]
    ) -> List[Dict[str, Any]]:
        sorted_analyses = sorted(
            analyses,
            key=lambda a: a.score.total_score,
            reverse=True
        )[:5]
        
        result = []
        for analysis in sorted_analyses:
            candidate = next(
                (c for c in candidates if c.id == analysis.candidate_id),
                None
            )
            if candidate:
                result.append({
                    "url": candidate.image_url,
                    "score": round(analysis.score.total_score, 1),
                    "verdict": analysis.score.final_verdict,
                    "domain": candidate.source_domain
                })
        
        return result
    
    async def cleanup(self):
        await self.search_service.close()
        await self.downloader.close()
