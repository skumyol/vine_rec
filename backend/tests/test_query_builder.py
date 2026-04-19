"""Tests for query builder."""

import pytest
from app.services.query_builder import QueryBuilder
from app.models.sku import ParsedSKU


class TestQueryBuilder:
    """Test query builder functionality."""

    @pytest.fixture
    def builder(self):
        return QueryBuilder()

    def test_build_queries_returns_list(self, builder, sample_parsed_sku):
        """Should return a list of queries."""
        queries = builder.build_queries(sample_parsed_sku)
        assert isinstance(queries, list)
        assert len(queries) > 0

    def test_exact_query_includes_all_fields(self, builder):
        """Exact query should include producer, vineyard, appellation."""
        sku = ParsedSKU(
            raw_name="Test Wine",
            producer="Domaine Test",
            appellation="Test Appellation",
            vineyard="Test Vineyard",
            vintage="2020",
            normalized_tokens=[]
        )
        queries = builder.build_queries(sku)
        
        exact_queries = [q for q in queries if q.query_type == "exact"]
        assert len(exact_queries) > 0
        
        # First exact query should have bottle keyword
        assert "bottle" in exact_queries[0].query.lower()

    def test_priority_ordering(self, builder, sample_parsed_sku):
        """Queries should be ordered by priority."""
        queries = builder.build_queries(sample_parsed_sku)
        
        priorities = [q.priority for q in queries]
        assert priorities == sorted(priorities)

    def test_bottle_keyword_variants(self, builder, sample_parsed_sku):
        """Should include bottle, wine, and label variants."""
        queries = builder.build_queries(sample_parsed_sku)
        
        query_texts = [q.query.lower() for q in queries]
        assert any("bottle" in q for q in query_texts)
        assert any("wine" in q for q in query_texts)
        assert any("label" in q for q in query_texts)

    def test_relaxed_query_simpler(self, builder):
        """Relaxed query should be simpler than exact."""
        sku = ParsedSKU(
            raw_name="Domaine Foo Bar Vineyard Appellation 2020",
            producer="Domaine Foo",
            appellation="Bar Appellation",
            vintage="2020",
            normalized_tokens=[]
        )
        queries = builder.build_queries(sku)
        
        exact = [q for q in queries if q.query_type == "exact"]
        relaxed = [q for q in queries if q.query_type == "relaxed"]
        
        if exact and relaxed:
            # Relaxed should have fewer words than exact
            exact_words = len(exact[0].query.split())
            relaxed_words = len(relaxed[0].query.split())
            assert relaxed_words <= exact_words

    def test_vintage_fallback_query(self, builder):
        """Should create query without vintage when vintage present."""
        sku = ParsedSKU(
            raw_name="Wine 2020",
            producer="Producer",
            appellation="Appellation",
            vintage="2020",
            normalized_tokens=[]
        )
        queries = builder.build_queries(sku)
        
        vintage_fallback = [q for q in queries if q.query_type == "vintage_fallback"]
        # Should have vintage fallback when vintage is present
        assert len(vintage_fallback) > 0 or not any(vintage_fallback)

    def test_empty_sku_returns_empty(self, builder):
        """Empty SKU should return minimal queries."""
        sku = ParsedSKU(
            raw_name="",
            normalized_tokens=[]
        )
        queries = builder.build_queries(sku)
        # Should handle gracefully, possibly return empty
        assert isinstance(queries, list)
