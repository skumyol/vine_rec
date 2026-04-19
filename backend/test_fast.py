#!/usr/bin/env python3
"""
Fast test script for VinoBuzz Assignment - Uses OpenCV + OCR only (no VLM)
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from app.models.sku import WineSKUInput, AnalysisRequest
from app.services.pipeline import AnalysisPipeline


@dataclass
class TestSKU:
    name: str
    vintage: str
    format: str
    region: str
    difficulty: str


TEST_SKUS = [
    TestSKU("Domaine Rossignol-Trapet Latricieres-Chambertin Grand Cru", "2017", "750ml", "Burgundy", "Hard"),
    TestSKU("Domaine Arlaud Morey-St-Denis 'Monts Luisants' 1er Cru", "2019", "750ml", "Burgundy", "Hard"),
    TestSKU("Domaine Taupenot-Merme Charmes-Chambertin Grand Cru", "2018", "750ml", "Burgundy", "Hard"),
    TestSKU("Château Fonroque Saint-Émilion Grand Cru Classé", "2016", "750ml", "Bordeaux", "Medium"),
    TestSKU("Eric Rodez Cuvée des Crayères Blanc de Noirs", "NV", "750ml", "Champagne", "Medium"),
    TestSKU("Domaine du Tunnel Cornas 'Vin Noir'", "2018", "750ml", "Northern Rhône", "Hard"),
    TestSKU("Poderi Colla Barolo 'Bussia Dardi Le Rose'", "2016", "750ml", "Piedmont", "Medium"),
    TestSKU("Arnot-Roberts Trousseau Gris Watson Ranch", "2020", "750ml", "Sonoma", "Very Hard"),
    TestSKU("Brokenwood Graveyard Vineyard Shiraz", "2015", "750ml", "Hunter Valley", "Medium"),
    TestSKU("Domaine Weinbach Riesling 'Clos des Capucins' Vendanges Tardives", "2017", "750ml", "Alsace", "Hard"),
]


@dataclass
class TestResult:
    sku_name: str
    vintage: str
    region: str
    difficulty: str
    verdict: str
    confidence: float
    selected_image_url: Optional[str]
    reason: str
    processing_time_ms: int
    top_candidates: List[Dict[str, Any]]


class FastEvaluator:
    def __init__(self, analyzer_mode: str = "opencv_only"):
        self.analyzer_mode = analyzer_mode
        self.pipeline = AnalysisPipeline()
        self.results: List[TestResult] = []
    
    async def run(self) -> List[TestResult]:
        print("=" * 80)
        print("VINOBUZZ ASSIGNMENT - FAST EVALUATION (OpenCV + OCR)")
        print("=" * 80)
        print(f"Mode: {self.analyzer_mode}")
        print(f"SKUs: {len(TEST_SKUS)}")
        print("=" * 80)
        
        total_start = time.perf_counter()
        
        for idx, sku in enumerate(TEST_SKUS, 1):
            print(f"\n[{idx}/10] {sku.name}")
            print(f"      {sku.vintage} | {sku.region} | {sku.difficulty}")
            
            result = await self._test_one(sku)
            self.results.append(result)
            
            icon = "✓" if result.verdict == "PASS" else "✗" if result.verdict in ["FAIL", "NO_IMAGE"] else "?"
            print(f"      {icon} {result.verdict} | conf: {result.confidence:.1f} | time: {result.processing_time_ms/1000:.1f}s")
            if result.selected_image_url:
                domain = result.selected_image_url.split('/')[2] if '/' in result.selected_image_url else 'unknown'
                print(f"      → {domain}")
            
            await asyncio.sleep(0.5)
        
        self._print_summary(time.perf_counter() - total_start)
        return self.results
    
    async def _test_one(self, sku: TestSKU) -> TestResult:
        request = AnalysisRequest(
            wine_name=sku.name,
            vintage=sku.vintage,
            format=sku.format,
            region=sku.region,
            analyzer_mode=self.analyzer_mode
        )
        
        try:
            result = await self.pipeline.analyze(request)
            return TestResult(
                sku_name=sku.name,
                vintage=sku.vintage,
                region=sku.region,
                difficulty=sku.difficulty,
                verdict=result.verdict,
                confidence=result.confidence,
                selected_image_url=result.selected_image_url,
                reason=result.reason[:100],
                processing_time_ms=result.processing_time_ms or 0,
                top_candidates=result.top_candidates[:3]
            )
        except Exception as e:
            return TestResult(
                sku_name=sku.name, vintage=sku.vintage, region=sku.region,
                difficulty=sku.difficulty, verdict="ERROR", confidence=0.0,
                selected_image_url=None, reason=str(e)[:100],
                processing_time_ms=0, top_candidates=[]
            )
    
    def _print_summary(self, total_time: float):
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        pass_count = sum(1 for r in self.results if r.verdict == "PASS")
        review_count = sum(1 for r in self.results if r.verdict == "REVIEW")
        fail_count = sum(1 for r in self.results if r.verdict in ["FAIL", "NO_IMAGE"])
        error_count = sum(1 for r in self.results if r.verdict == "ERROR")
        
        print(f"\nPASS:     {pass_count}/10 ({pass_count*10}%)")
        print(f"REVIEW:   {review_count}/10")
        print(f"FAIL:     {fail_count}/10")
        print(f"ERROR:    {error_count}/10")
        
        avg_time = sum(r.processing_time_ms for r in self.results) / len(self.results) / 1000
        print(f"\nTotal time: {total_time:.1f}s")
        print(f"Avg per SKU: {avg_time:.1f}s")
        
        print(f"\n{'#':<4} {'Wine':<45} {'Diff':<10} {'Result':<10} {'Conf':<8} {'Time'}")
        print("-" * 90)
        for i, r in enumerate(self.results, 1):
            name = r.sku_name[:43] + ".." if len(r.sku_name) > 45 else r.sku_name
            print(f"{i:<4} {name:<45} {r.difficulty:<10} {r.verdict:<10} {r.confidence:<8.1f} {r.processing_time_ms/1000:.1f}s")
        
        print("\n" + "=" * 80)
        print(f"TARGET: 90% | ACTUAL: {pass_count*10}%")
        if pass_count >= 9:
            print("✓ TARGET ACHIEVED")
        else:
            print("✗ Review failures above")
        print("=" * 80)
    
    def export(self, filename: str = None):
        if not filename:
            filename = f"fast_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "mode": self.analyzer_mode,
            "summary": {
                "pass": sum(1 for r in self.results if r.verdict == "PASS"),
                "review": sum(1 for r in self.results if r.verdict == "REVIEW"),
                "fail": sum(1 for r in self.results if r.verdict in ["FAIL", "NO_IMAGE"]),
            },
            "results": [asdict(r) for r in self.results]
        }
        
        import os
        os.makedirs("../data/results", exist_ok=True)
        path = f"../data/results/{filename}"
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nExported: {path}")
        return path
    
    async def cleanup(self):
        await self.pipeline.cleanup()


async def main():
    evaluator = FastEvaluator(analyzer_mode="opencv_only")
    try:
        await evaluator.run()
        evaluator.export()
    finally:
        await evaluator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
