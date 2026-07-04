"""Process uploaded claim documents and photos.

Turns raw uploads (claim narrative, police report / FIR, PDFs, damage photos)
into the inputs the investigation pipeline needs:
  - text is extracted from .txt / .pdf files,
  - photos are perceptual-hashed and EXIF-checked (and matched against stored
    hashes for reuse), and optionally read by a vision model for a damage
    description and photo-vs-narrative consistency.
"""

from __future__ import annotations

import io
from typing import Any

from insurclaim.db import repo


def extract_text(filename: str, data: bytes) -> str:
    """Extract text from an uploaded .txt or .pdf file."""
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    return data.decode("utf-8", errors="ignore").strip()


def process_photo(filename: str, data: bytes) -> dict[str, Any]:
    """Perceptual-hash a photo, read its EXIF time, and flag reuse."""
    import imagehash
    from PIL import Image
    from PIL.ExifTags import TAGS

    image = Image.open(io.BytesIO(data))
    phash = str(imagehash.phash(image))

    captured_at = None
    for tag_id, value in image.getexif().items():
        if TAGS.get(tag_id) == "DateTime":
            captured_at = str(value)

    duplicates = repo.find_duplicate_photos(phash)
    return {
        "file_name": filename,
        "phash": phash,
        "captured_at": captured_at,
        "duplicate_of": duplicates[0] if duplicates else None,
    }


def analyze_damage(data: bytes, mime: str = "image/jpeg") -> str | None:
    """Describe the vehicle damage in a photo using a vision model.

    Returns None if the vision model is unavailable (e.g. no key / rate-limited).
    """
    from insurclaim.llm import call_vision

    prompt = (
        "You are an auto claims assessor. Describe the vehicle damage visible in "
        "this photo: which parts are damaged, the severity (minor / moderate / "
        "severe), and note anything that looks inconsistent or staged. Be concise."
    )
    try:
        return call_vision(prompt, data, mime=mime)
    except Exception:
        return None


def build_claim_text(documents: list[tuple[str, bytes]], photos: list[dict]) -> str:
    """Combine extracted document text and photo notes into one claim narrative."""
    parts = [extract_text(name, data) for name, data in documents]
    for photo in photos:
        note = f"[photo {photo['file_name']}]"
        if photo.get("duplicate_of"):
            note += " (WARNING: matches a photo already on another claim)"
        if photo.get("damage"):
            note += f" damage: {photo['damage']}"
        parts.append(note)
    return "\n\n".join(p for p in parts if p)
