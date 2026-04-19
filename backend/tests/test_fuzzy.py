"""Tests for fuzzy matching utilities."""

import pytest
from app.utils.fuzzy import (
    fuzzy_match,
    fuzzy_contains,
    similarity,
    partial_similarity,
    token_sort_similarity,
)


class TestFuzzyMatching:
    """Test fuzzy matching functionality."""

    def test_fuzzy_match_exact(self):
        """Should match exact string."""
        result = fuzzy_match("domaine", ["domaine", "chateau"])
        assert result is not None
        assert result[0] == "domaine"
        assert result[1] == 100.0

    def test_fuzzy_match_typo(self):
        """Should match with typo tolerance."""
        result = fuzzy_match("domane", ["domaine", "chateau"], threshold=80.0)
        assert result is not None
        assert result[0] == "domaine"

    def test_fuzzy_match_no_match(self):
        """Should return None when no good match."""
        result = fuzzy_match("xyz123", ["domaine", "chateau"], threshold=80.0)
        assert result is None

    def test_fuzzy_contains_substring(self):
        """Should find substring with fuzzy matching."""
        text = "Domaine de la Romanee Conti Grand Cru"
        # partial_ratio gives high scores for substrings
        assert fuzzy_contains(text, "romanee", threshold=80.0)

    def test_fuzzy_contains_no_substring(self):
        """Should return False when substring not present."""
        text = "Chateau Margaux"
        assert not fuzzy_contains(text, "romanee", threshold=80.0)

    def test_similarity_exact(self):
        """Exact match should be 1.0."""
        result = similarity("domaine", "domaine")
        assert result == 1.0

    def test_similarity_different(self):
        """Different strings should be low."""
        result = similarity("domaine", "chateau")
        assert result < 0.5

    def test_partial_similarity_substring(self):
        """Partial should work for substrings."""
        result = partial_similarity("romanee", "domaine de la romanee conti")
        assert result > 0.8

    def test_token_sort_similarity_order_independent(self):
        """Token sort should ignore word order."""
        result = token_sort_similarity(
            "conti romanee la de domaine",
            "domaine de la romanee conti"
        )
        assert result > 0.9

    def test_threshold_behavior(self):
        """Threshold should filter matches."""
        # High threshold - strict
        strict = fuzzy_match("domane", ["domaine"], threshold=95.0)
        # Low threshold - lenient
        lenient = fuzzy_match("domane", ["domaine"], threshold=60.0)
        
        assert strict is None  # Too strict
        assert lenient is not None  # Should match
