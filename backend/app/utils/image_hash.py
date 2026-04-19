"""Image hashing utilities for deduplication."""

import hashlib
from typing import Optional
from PIL import Image
import imagehash


def compute_file_hash(filepath: str) -> str:
    """Compute MD5 hash of file contents."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def compute_phash(image_path: str) -> Optional[str]:
    """
    Compute perceptual hash (pHash) for image.

    Returns:
        Hex string hash or None if failed
    """
    try:
        with Image.open(image_path) as img:
            phash = imagehash.phash(img)
            return str(phash)
    except Exception:
        return None


def compute_dhash(image_path: str) -> Optional[str]:
    """
    Compute difference hash (dHash) for image.

    Returns:
        Hex string hash or None if failed
    """
    try:
        with Image.open(image_path) as img:
            dhash = imagehash.dhash(img)
            return str(dhash)
    except Exception:
        return None


def hash_similarity(hash1: str, hash2: str) -> float:
    """
    Calculate similarity between two image hashes.

    Returns:
        Similarity score 0.0 to 1.0
    """
    if not hash1 or not hash2:
        return 0.0

    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        # Hamming distance normalized
        max_distance = len(hash1) * 4  # hex to binary
        distance = h1 - h2
        return 1.0 - (distance / max_distance)
    except Exception:
        return 0.0


def is_duplicate(hash1: str, hash2: str, threshold: float = 0.9) -> bool:
    """Check if two images are duplicates based on hash similarity."""
    return hash_similarity(hash1, hash2) >= threshold
