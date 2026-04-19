#!/usr/bin/env python3
"""Test a single SKU through the pipeline."""

import asyncio
import time
from app.services.pipeline import AnalysisPipeline
from app.models.sku import AnalysisRequest

async def test_single():
    """Test one SKU."""
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
    print("Starting analysis...")
    
    start = time.perf_counter()
    result = await pipeline.analyze(request)
    elapsed = time.perf_counter() - start
    
    print(f"\n=== RESULT ===")
    sku_name = f"{result.parsed_sku.producer or ''} {result.parsed_sku.appellation or ''} {result.parsed_sku.vineyard or ''}".strip()
    print(f"SKU: {sku_name}")
    print(f"Verdict: {result.verdict}")
    print(f"Confidence: {result.confidence:.1f}")
    print(f"Time: {elapsed:.1f}s")
    print(f"Reason: {result.reason}")
    print(f"Top candidates: {len(result.top_candidates)}")
    for c in result.top_candidates[:3]:
        print(f"  - Score: {c.get('score', 0):.1f}, Verdict: {c.get('verdict', 'N/A')}, URL: {c.get('url', 'N/A')[:60]}...")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test_single())
