#!/usr/bin/env python3
"""Debug scoring details for a single SKU."""

import asyncio
import time
from app.services.pipeline import AnalysisPipeline
from app.models.sku import AnalysisRequest

async def test_single():
    """Test one SKU with detailed debugging."""
    print("Initializing pipeline...")
    pipeline = AnalysisPipeline()
    
    request = AnalysisRequest(
        wine_name="Château Fonroque Saint-Émilion Grand Cru Classé",
        vintage="2016",
        format="750ml",
        region="Bordeaux",
        analyzer_mode="hybrid_fast"
    )
    
    print(f"Testing: {request.wine_name}")
    print("Starting analysis...\n")
    
    start = time.perf_counter()
    
    # Parse SKU (parser expects AnalysisRequest)
    parsed_sku = pipeline.parser.parse(request)
    print(f"Parsed SKU: {parsed_sku.producer} | {parsed_sku.appellation} | {parsed_sku.vintage}")
    
    # Build queries
    queries = pipeline.query_builder.build_queries(parsed_sku)
    print(f"Generated {len(queries)} search queries")
    for q in queries:
        print(f"  - {q.query}")
    
    # Search for candidates
    print("\nSearching for candidates...")
    candidates = await pipeline.search_service.search_candidates(parsed_sku, queries)
    print(f"Found {len(candidates)} candidates")
    
    if not candidates:
        print("No candidates found!")
        return
    
    # Download first candidate only for debugging
    candidate = candidates[0]
    print(f"\nTesting first candidate: {candidate.image_url[:80]}...")
    
    # Download
    downloaded = await pipeline.downloader.download(candidate)
    print(f"Download status: {downloaded.download_status}")
    
    if downloaded.download_status not in ("downloaded", "cached"):
        print("Download failed!")
        return
    
    # Preprocess
    preprocessed = pipeline.preprocessor.preprocess(downloaded)
    print(f"Preprocessed: {preprocessed.local_path}")
    
    # OpenCV analysis
    print("\n--- OpenCV Analysis ---")
    opencv_result = pipeline.opencv_filter.analyze(preprocessed)
    print(f"  opencv_pass: {opencv_result.opencv_pass}")
    print(f"  sharpness_score: {opencv_result.sharpness_score:.1f}")
    print(f"  single_bottle: {opencv_result.single_bottle}")
    print(f"  upright: {opencv_result.upright}")
    print(f"  label_visible: {opencv_result.label_visible}")
    print(f"  rejection_reason: {opencv_result.rejection_reason}")
    
    # Get bottle bbox and crops
    bottle_bbox = pipeline.opencv_filter.get_bottle_bbox(preprocessed)
    crops = pipeline.label_cropper.extract_crops(preprocessed, bottle_bbox)
    print(f"\nCrops: {list(crops.keys())}")
    
    # OCR
    print("\n--- OCR Analysis ---")
    ocr_result = pipeline.ocr_service.extract_text(preprocessed, crops)
    print(f"  Raw text length: {len(ocr_result.raw_text)}")
    print(f"  Raw text preview: {ocr_result.raw_text[:200]}...")
    
    # Text matching
    print("\n--- Text Matching ---")
    text_score, field_matches, hard_fails = pipeline.matcher.match(parsed_sku, ocr_result)
    print(f"  Text score: {text_score:.1f}")
    print(f"  Field matches: {field_matches}")
    print(f"  Hard fails: {hard_fails}")
    
    # VLM
    print("\n--- VLM Analysis ---")
    gemini_result = None
    if pipeline.gemini_verifier.is_available():
        print("  Calling Gemini...")
        gemini_result = await pipeline.gemini_verifier.verify(
            preprocessed.local_path, parsed_sku, ocr_result.raw_text
        )
        if gemini_result:
            print(f"  Gemini producer_match: {gemini_result.producer_match}")
            print(f"  Gemini confidence: {gemini_result.confidence:.1f}")
            print(f"  Gemini vintage_match: {gemini_result.vintage_match}")
    else:
        print("  Gemini not available")
    
    # Score
    print("\n--- Final Scoring ---")
    score = pipeline.scorer.score(
        opencv_result=opencv_result,
        ocr_result=ocr_result,
        gemini_result=gemini_result,
        qwen_result=None,
        text_verification_score=text_score,
        field_matches=field_matches,
        hard_fails=hard_fails
    )
    print(f"  Total score: {score.total_score:.1f}")
    print(f"  Verdict: {score.final_verdict}")
    print(f"  Thresholds: pass={pipeline.scorer.pass_threshold}, review={pipeline.scorer.review_threshold}")
    
    elapsed = time.perf_counter() - start
    print(f"\nTotal time: {elapsed:.1f}s")

if __name__ == "__main__":
    asyncio.run(test_single())
