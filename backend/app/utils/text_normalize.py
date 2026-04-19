"""Text normalization utilities for wine name matching."""

import re
import unicodedata
from typing import List


# Wine-specific term mappings
CRU_NORMALIZATIONS = {
    '1er cru': 'premier cru',
    '1er': 'premier',
    '1ère': 'premier',
    'grand cru': 'grand cru',
    'gc': 'grand cru',
}

SAINT_NORMALIZATIONS = {
    'st ': 'saint ',
    'ste ': 'sainte ',
}

APPELLATION_ABBREVIATIONS = {
    'msd': 'morey saint denis',
    'gevrey': 'gevrey-chambertin',
    'chambolle': 'chambolle-musigny',
    'vosne': 'vosne-romanee',
    'nuit': 'nuits-saint-georges',
    'beaune': 'cote de beaune',
    'pommard': 'pommard',
    'volnay': 'volnay',
    'meursault': 'meursault',
}


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.

    Steps:
    1. Convert to lowercase
    2. Remove accents
    3. Normalize hyphens and punctuation
    4. Normalize whitespace
    5. Apply wine-specific normalizations
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove accents
    text = remove_accents(text)

    # Normalize hyphens
    text = text.replace("'", " ")
    text = text.replace("-", " ")

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Apply wine-specific normalizations
    text = normalize_cru_terms(text)
    text = normalize_saint_terms(text)

    return text


def remove_accents(text: str) -> str:
    """Remove accents from text."""
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )


def normalize_cru_terms(text: str) -> str:
    """Normalize Premier Cru / Grand Cru terms."""
    # Sort by length (longest first) to avoid partial replacements
    items = sorted(CRU_NORMALIZATIONS.items(), key=lambda x: -len(x[0]))
    for abbr, full in items:
        pattern = r'\b' + re.escape(abbr) + r'\b'
        text = re.sub(pattern, full, text)
    return text


def normalize_saint_terms(text: str) -> str:
    """Normalize Saint/St abbreviations."""
    # Handle hyphenated forms with regex to avoid replacing 'st' inside words
    text = re.sub(r'\bst-', 'saint ', text)
    text = re.sub(r'\bste-', 'sainte ', text)
    text = re.sub(r'-st-', ' saint ', text)
    text = re.sub(r'-ste-', ' sainte ', text)
    # Handle space-separated
    text = re.sub(r'\bst\s', 'saint ', text)
    text = re.sub(r'\bste\s', 'sainte ', text)
    # Handle end of string
    text = re.sub(r'\bst$', 'saint', text)
    text = re.sub(r'\bste$', 'sainte', text)
    return text


def tokenize(text: str) -> List[str]:
    """Tokenize text into normalized tokens."""
    normalized = normalize_text(text)
    # Split on whitespace and filter short tokens
    tokens = normalized.split()
    return [t for t in tokens if len(t) > 1]


def create_ngrams(tokens: List[str], n: int = 2) -> List[str]:
    """Create n-grams from tokens."""
    if len(tokens) < n:
        return [' '.join(tokens)]
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def normalize_vintage(text: str) -> str:
    """Extract and normalize vintage year."""
    # Match 4-digit years (19xx or 20xx)
    match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    return match.group(1) if match else ""
