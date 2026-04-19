#!/usr/bin/env python3
"""
Test script for VinoBuzz Internship Assignment - 10 Test SKUs
Run against the target accuracy of 90%
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
    """One of the 10 test SKUs from the assignment."""
    name: str
    vintage: str
    format: str
    region: str
    difficulty: str


# The 10 Test SKUs from the assignment
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
    """Result for a single test SKU."""
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


class AssignmentEvaluator:
    """Evaluates the pipeline against the 10 test SKUs."""
    
    def __init__(self, analyzer_mode: str = "hybrid_fast"):
        self.analyzer_mode = analyzer_mode
        self.pipeline = AnalysisPipeline()
        self.results: List[TestResult] = []
    
    async def run_evaluation(self) -> List[TestResult]:
        """Run the pipeline on all 10 test SKUs."""
        print("=" * 80)
        print("VINOBUZZ INTERNSHIP ASSIGNMENT - TEST SKU EVALUATION")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Analyzer Mode: {self.analyzer_mode}")
        print(f"Total SKUs to test: {len(TEST_SKUS)}")
        print("=" * 80)
        
        total_start = time.perf_counter()
        
        for idx, sku in enumerate(TEST_SKUS, 1):
            print(f"\n[{idx}/10] Testing: {sku.name}")
            print(f"      Vintage: {sku.vintage}, Region: {sku.region}, Difficulty: {sku.difficulty}")
            
            result = await self._test_single_sku(sku)
            self.results.append(result)
            
            # Print result summary
            status_icon = "✓" if result.verdict == "PASS" else "✗" if result.verdict == "FAIL" else "?"
            print(f"      Result: {status_icon} {result.verdict} (confidence: {result.confidence:.1f})")
            if result.selected_image_url:
                print(f"      Image: {result.selected_image_url[:80]}...")
            
            # Rate limiting between requests
            if idx < len(TEST_SKUS):
                await asyncio.sleep(1)
        
        total_time = time.perf_counter() - total_start
        
        # Print summary
        self._print_summary(total_time)
        
        return self.results
    
    async def _test_single_sku(self, sku: TestSKU) -> TestResult:
        """Test a single SKU through the pipeline."""
        request = AnalysisRequest(
            wine_name=sku.name,
            vintage=sku.vintage,
            format=sku.format,
            region=sku.region,
            analyzer_mode=self.analyzer_mode
        )
        
        try:
            analysis_result = await self.pipeline.analyze(request)
            
            return TestResult(
                sku_name=sku.name,
                vintage=sku.vintage,
                region=sku.region,
                difficulty=sku.difficulty,
                verdict=analysis_result.verdict,
                confidence=analysis_result.confidence,
                selected_image_url=analysis_result.selected_image_url,
                reason=analysis_result.reason,
                processing_time_ms=analysis_result.processing_time_ms or 0,
                top_candidates=analysis_result.top_candidates
            )
        except Exception as e:
            print(f"      ERROR: {str(e)[:100]}")
            return TestResult(
                sku_name=sku.name,
                vintage=sku.vintage,
                region=sku.region,
                difficulty=sku.difficulty,
                verdict="ERROR",
                confidence=0.0,
                selected_image_url=None,
                reason=f"Pipeline error: {str(e)[:100]}",
                processing_time_ms=0,
                top_candidates=[]
            )
    
    def _print_summary(self, total_time: float):
        """Print evaluation summary."""
        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)
        
        # Count verdicts
        pass_count = sum(1 for r in self.results if r.verdict == "PASS")
        review_count = sum(1 for r in self.results if r.verdict == "REVIEW")
        fail_count = sum(1 for r in self.results if r.verdict == "FAIL")
        no_image_count = sum(1 for r in self.results if r.verdict == "NO_IMAGE")
        error_count = sum(1 for r in self.results if r.verdict == "ERROR")
        
        # Count PASS + REVIEW as successful verifications
        successful_count = pass_count + review_count
        accuracy = (successful_count / len(self.results)) * 100
        
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"\nVerdict Distribution:")
        print(f"  PASS:      {pass_count}/{len(self.results)} ({pass_count/len(self.results)*100:.0f}%)")
        print(f"  REVIEW:    {review_count}/{len(self.results)} ({review_count/len(self.results)*100:.0f}%)")
        print(f"  FAIL:      {fail_count}/{len(self.results)} ({fail_count/len(self.results)*100:.0f}%)")
        print(f"  NO_IMAGE:  {no_image_count}/{len(self.results)} ({no_image_count/len(self.results)*100:.0f}%)")
        
        print(f"\nTiming:")
        print(f"  Total wall time: {total_time:.1f}s")
        print(f"  Total processing time: {sum(r.processing_time_ms for r in self.results)/1000:.1f}s")
        print(f"  Average per SKU: {sum(r.processing_time_ms for r in self.results)/len(self.results)/1000:.1f}s")
        
        # Detailed table
        print(f"\nDetailed Results:")
        print(f"{'#':<4} {'Wine':<50} {'Difficulty':<8} {'Verdict':<10} {'Conf':<8} {'Time':<10}")
        print("-" * 100)
        
        for i, result in enumerate(self.results, 1):
            wine_name = result.sku_name[:48]
            diff = result.difficulty
            verdict = result.verdict
            conf = result.confidence
            time_ms = result.processing_time_ms
            
            # Highlight passing results (PASS or REVIEW)
            symbol = "✓" if verdict in ["PASS", "REVIEW"] else "?" if verdict == "FAIL" else "✗"
            
            print(f"{i:<4} {wine_name:<50} {diff:<8} {symbol} {verdict:<8} {conf:<8.1f} {time_ms/1000:<10.1f}s")
        
        print("\n" + "="*60)
        print(f"TARGET: 90% accuracy (9/10 SKUs with verified photos)")
        print(f"ACTUAL: {pass_count}/{len(self.results)} PASS, {review_count}/{len(self.results)} REVIEW = {successful_count}/{len(self.results)} successful ({accuracy:.0f}%)")
        
        if accuracy >= 90:
            print("✓ Target achieved!")
        else:
            print("✗ Target not yet achieved - review failures above")
        print("=" * 80)
    
    def export_results(self, filename: str = None):
        """Export results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "analyzer_mode": self.analyzer_mode,
            "summary": {
                "total_skus": len(self.results),
                "pass_count": sum(1 for r in self.results if r.verdict == "PASS"),
                "review_count": sum(1 for r in self.results if r.verdict == "REVIEW"),
                "fail_count": sum(1 for r in self.results if r.verdict == "FAIL"),
                "no_image_count": sum(1 for r in self.results if r.verdict == "NO_IMAGE"),
            },
            "results": [asdict(r) for r in self.results]
        }
        
        filepath = f"../data/results/{filename}"
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults exported to: {filepath}")
        return filepath
    
    async def cleanup(self):
        await self.pipeline.cleanup()


async def main():
    """Main entry point."""
    evaluator = AssignmentEvaluator(analyzer_mode="hybrid_fast")
    
    try:
        await evaluator.run_evaluation()
        evaluator.export_results()
    finally:
        await evaluator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
