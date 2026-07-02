"""Image-based fraud checks - pure code, no LLM.

Two ideas:
1. EXIF metadata sanity: read the capture time from a photo's metadata.
2. Perceptual hashing: compute a fingerprint that stays similar when an image
   is lightly edited/resized, so the same damage photo reused across claims can
   be detected even if it is not byte-identical.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image
from PIL.ExifTags import TAGS
import imagehash

from insurclaim.db import repo


def compute_phash(image_path: str | Path) -> str:
    """Return the perceptual hash of an image as a hex string."""
    with Image.open(image_path) as img:
        return str(imagehash.phash(img))


def read_capture_time(image_path: str | Path) -> str | None:
    """Return the photo's capture time from EXIF metadata, if present."""
    with Image.open(image_path) as img:
        exif = img.getexif()
        for tag_id, value in exif.items():
            if TAGS.get(tag_id) == "DateTime":
                return str(value)
    return None


def find_reused_photo(image_path: str | Path, exclude_claim_id: int | None = None) -> dict[str, Any] | None:
    """Check whether this photo's hash already exists on another claim.

    Returns a fraud signal dict if a duplicate is found, otherwise None.
    """
    phash = compute_phash(image_path)
    duplicates = repo.find_duplicate_photos(phash, exclude_claim_id=exclude_claim_id)
    if not duplicates:
        return None
    other = duplicates[0]
    return {
        "code": "duplicate_photo",
        "message": "This damage photo was already used on another claim.",
        "evidence": f"phash={phash}, matches claim_id={other['claim_id']} ({other['file_name']})",
        "severity": "high",
    }


def check_images(image_paths: list[str | Path], exclude_claim_id: int | None = None) -> list[dict[str, Any]]:
    """Run image checks over a list of photos and return any fraud signals."""
    signals: list[dict[str, Any]] = []
    for path in image_paths:
        signal = find_reused_photo(path, exclude_claim_id=exclude_claim_id)
        if signal:
            signals.append(signal)
    return signals
