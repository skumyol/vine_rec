"""Fuzzy matching utilities."""

from typing import List, Tuple, Optional
from rapidfuzz import fuzz, process


def fuzzy_match(
    query: str,
    choices: List[str],
    threshold: float = 70.0,
    scorer=fuzz.WRatio
) -> Optional[Tuple[str, float]]:
    """
    Find best fuzzy match from choices.

    Returns:
        Tuple of (match, score) or None if no match above threshold
    """
    result = process.extractOne(query, choices, scorer=scorer)
    if result:
        match, score, _ = result
        if score >= threshold:
            return match, score
    return None


def fuzzy_contains(
    text: str,
    substring: str,
    threshold: float = 80.0
) -> bool:
    """Check if text contains substring with fuzzy matching."""
    # Use partial_ratio for substring matching
    score = fuzz.partial_ratio(substring, text)
    return score >= threshold


def similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings."""
    return fuzz.ratio(a, b) / 100.0


def partial_similarity(a: str, b: str) -> float:
    """Calculate partial similarity (good for substrings)."""
    return fuzz.partial_ratio(a, b) / 100.0


def token_sort_similarity(a: str, b: str) -> float:
    """Calculate similarity ignoring word order."""
    return fuzz.token_sort_ratio(a, b) / 100.0
