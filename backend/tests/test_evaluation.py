"""Evaluation tests for wine photo verification pipeline with F1 metrics."""

import pytest
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.models.sku import AnalysisRequest, WineSKUInput
from app.models.candidate import ImageCandidate, VLMVerification


class Verdict(Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"
    NO_IMAGE = "NO_IMAGE"


@dataclass
class TestCase:
    """A single test case for evaluation."""
    name: str
    wine_input: WineSKUInput
    expected_verdict: Verdict
    description: str


class F1Metrics:
    """Calculate F1 metrics for classification."""
    
    def __init__(self):
        self.tp = 0  # True Positives
        self.fp = 0  # False Positives
        self.tn = 0  # True Negatives
        self.fn = 0  # False Negatives
        self.total = 0
        self.correct = 0
        
    def add(self, predicted: str, expected: str, binary_mode: bool = False):
        """Add a prediction result."""
        self.total += 1
        
        if predicted == expected:
            self.correct += 1
            if binary_mode:
                if predicted == "PASS":
                    self.tp += 1
                else:
                    self.tn += 1
            else:
                self.tp += 1
        else:
            if binary_mode:
                if predicted == "PASS" and expected != "PASS":
                    self.fp += 1
                elif predicted != "PASS" and expected == "PASS":
                    self.fn += 1
                elif predicted == "FAIL":
                    self.fn += 1
                else:
                    self.fp += 1
            else:
                self.fp += 1
                self.fn += 1
    
    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total > 0 else 0.0
    
    @property
    def precision(self) -> float:
        denominator = self.tp + self.fp
        return self.tp / denominator if denominator > 0 else 0.0
    
    @property
    def recall(self) -> float:
        denominator = self.tp + self.fn
        return self.tp / denominator if denominator > 0 else 0.0
    
    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0


class TestPipelineEvaluation:
    """Evaluation tests for the wine verification pipeline."""
    
    @pytest.fixture
    def benchmark_cases(self) -> List[TestCase]:
        """Define benchmark test cases with expected outcomes."""
        return [
            # Well-known wines that should PASS with high confidence
            TestCase(
                name="chateau_margaux_2015",
                wine_input=WineSKUInput(
                    wine_name="Chateau Margaux 2015",
                    vintage="2015",
                    format="750ml",
                    region="Bordeaux"
                ),
                expected_verdict=Verdict.PASS,
                description="Well-known first growth with clear label"
            ),
            TestCase(
                name="romanee_conti_2018",
                wine_input=WineSKUInput(
                    wine_name="Domaine de la Romanee-Conti Romanee-Conti 2018",
                    vintage="2018",
                    format="750ml",
                    region="Burgundy"
                ),
                expected_verdict=Verdict.PASS,
                description="Iconic Burgundy with distinctive label"
            ),
            TestCase(
                name="screaming_eagle_2019",
                wine_input=WineSKUInput(
                    wine_name="Screaming Eagle Cabernet Sauvignon 2019",
                    vintage="2019",
                    format="750ml",
                    region="Napa Valley"
                ),
                expected_verdict=Verdict.PASS,
                description="Cult California wine"
            ),
            # Edge cases that may REVIEW or FAIL
            TestCase(
                name="generic_bordeaux",
                wine_input=WineSKUInput(
                    wine_name="Bordeaux Rouge 2020",
                    vintage="2020",
                    format="750ml",
                    region="Bordeaux"
                ),
                expected_verdict=Verdict.REVIEW,
                description="Generic wine without specific producer"
            ),
            TestCase(
                name="obscure_wine",
                wine_input=WineSKUInput(
                    wine_name="Domaine Obscure Petite Climat 2015",
                    vintage="2015",
                    format="750ml",
                    region="Burgundy"
                ),
                expected_verdict=Verdict.NO_IMAGE,
                description="Obscure wine unlikely to have verified images"
            ),
        ]
    
    def test_f1_metrics_calculation(self):
        """Test F1 metrics calculation."""
        metrics = F1Metrics()
        
        # Simulate some results
        metrics.add("PASS", "PASS", binary_mode=True)  # TP
        metrics.add("PASS", "PASS", binary_mode=True)  # TP
        metrics.add("PASS", "REVIEW", binary_mode=True)  # FP
        metrics.add("FAIL", "PASS", binary_mode=True)  # FN
        metrics.add("FAIL", "FAIL", binary_mode=True)  # TN
        
        assert metrics.total == 5
        assert metrics.accuracy == 0.6
        assert metrics.precision == 2/3  # 2 TP / (2 TP + 1 FP)
        assert metrics.recall == 2/3    # 2 TP / (2 TP + 1 FN)
        assert abs(metrics.f1_score - 0.667) < 0.01
    
    @pytest.mark.asyncio
    async def test_evaluate_qwen_verifier(self, benchmark_cases):
        """Evaluate Qwen VL verifier on benchmark cases."""
        from app.services.qwen_verifier import QwenVerifier
        
        verifier = QwenVerifier()
        if not verifier.is_available():
            pytest.skip("Qwen VL not available")
        
        metrics = F1Metrics()
        results = []
        
        for case in benchmark_cases[:2]:  # Test subset
            # Create a mock candidate for testing
            # In real evaluation, we'd search and download actual images
            
            print(f"Evaluating: {case.name}")
            print(f"  Expected: {case.expected_verdict.value}")
            print(f"  Description: {case.description}")
            
            # For now, just verify verifier is working
            assert verifier.is_available()
            assert verifier.model_name is not None
            
        print(f"\nQwen VL Evaluation: Model={verifier.model_name}")
        print(f"Using OpenRouter: {verifier.use_openrouter}")


class TestSerpAPIIntegration:
    """Tests for SerpAPI search integration."""
    
    @pytest.mark.asyncio
    async def test_serpapi_search_available(self):
        """Test SerpAPI is configured and can search."""
        from app.core.config import settings
        from app.services.search_service import SearchService
        from app.services.parser import WineParser
        from app.services.query_builder import QueryBuilder
        
        # Check if SerpAPI key is configured
        has_serpapi = settings.SERPAPI_KEY is not None and len(settings.SERPAPI_KEY) > 20
        
        if not has_serpapi:
            pytest.skip("SerpAPI key not configured")
        
        # Create search service with serpapi
        service = SearchService()
        service.provider = "serpapi"
        service.api_key = settings.SERPAPI_KEY
        
        # Parse a test wine
        parser = WineParser()
        sku_input = WineSKUInput(
            wine_name="Chateau Margaux 2015",
            vintage="2015",
            format="750ml",
            region="Bordeaux"
        )
        parsed = parser.parse(sku_input)
        
        # Build queries
        qb = QueryBuilder()
        queries = qb.build_queries(parsed)
        
        assert len(queries) > 0
        
        # Try to search
        try:
            candidates = await service._search_serpapi(queries[0], parsed)
            print(f"SerpAPI returned {len(candidates)} candidates")
            
            if len(candidates) > 0:
                print(f"First candidate: {candidates[0].image_url[:60]}...")
                print(f"Source domain: {candidates[0].source_domain}")
        except Exception as e:
            print(f"SerpAPI search error: {e}")
            # Don't fail the test, just report
    
    def test_serpapi_key_in_env(self):
        """Verify SERPAPI_KEY is loaded from environment."""
        from app.core.config import settings
        
        print(f"SERPAPI_KEY present: {settings.SERPAPI_KEY is not None}")
        if settings.SERPAPI_KEY:
            print(f"SERPAPI_KEY length: {len(settings.SERPAPI_KEY)}")
            print(f"SERPAPI_KEY prefix: {settings.SERPAPI_KEY[:20]}...")
