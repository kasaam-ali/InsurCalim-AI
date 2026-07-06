"""Process uploaded claim documents, photos, and videos.

Turns raw uploads (claim narrative, police report / FIR, PDFs, Word documents,
damage photos, and dashcam / walkaround videos) into the inputs the
investigation pipeline needs:
  - text is extracted from .txt / .pdf / .docx files,
  - photos are perceptual-hashed and EXIF-checked (and matched against stored
    hashes for reuse), and optionally read by a vision model for a damage
    description and photo-vs-narrative consistency,
  - videos are sampled (middle frame), then treated like a photo for damage
    analysis and duplicate-frame detection,
  - photos / video frames are screened for signs of being AI-generated
    (deepfake / GenAI fraud) via metadata forensics + a vision-model check.
"""

from __future__ import annotations

import io
from typing import Any

from insurclaim.db import repo

# File extensions we know how to handle, grouped by how they are processed.
DOCUMENT_EXTS = {".txt", ".pdf", ".docx"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def classify_upload(filename: str) -> str:
    """Route an uploaded file by extension: document / image / video / unsupported."""
    name = filename.lower()
    if any(name.endswith(ext) for ext in DOCUMENT_EXTS):
        return "document"
    if any(name.endswith(ext) for ext in IMAGE_EXTS):
        return "image"
    if any(name.endswith(ext) for ext in VIDEO_EXTS):
        return "video"
    return "unsupported"


def extract_text(filename: str, data: bytes) -> str:
    """Extract text from an uploaded .txt / .pdf / .docx file."""
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if name.endswith(".docx"):
        import docx  # python-docx

        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs).strip()
    if name.endswith(".doc"):
        # Legacy binary Word (97-2003) is not supported; ask for PDF/DOCX instead.
        return ""
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


def process_video(filename: str, data: bytes) -> dict[str, Any]:
    """Sample the middle frame of a video and treat it like a photo.

    Reads basic metadata (frame count, duration), grabs the middle frame,
    perceptual-hashes it (for duplicate-frame reuse), and returns the frame as
    JPEG bytes so the caller can run the vision damage / synthetic-media checks.
    If the codec can't be read, returns metadata-only without raising.
    """
    import os
    import tempfile

    result: dict[str, Any] = {
        "file_name": filename,
        "kind": "video",
        "duration_s": None,
        "frames": 0,
        "phash": None,
        "captured_at": None,
        "duplicate_of": None,
        "frame_jpeg": None,
    }

    suffix = os.path.splitext(filename)[1] or ".mp4"
    tmp_path = None
    frame = None
    try:
        import cv2

        # OpenCV's VideoCapture needs a file path, so buffer the bytes to a temp
        # file (and close it before reading — required on Windows).
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        result["frames"] = total
        result["duration_s"] = round(total / fps, 1) if fps else None
        if total:
            cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            frame = None
    except Exception:
        frame = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    if frame is not None:
        import cv2
        import imagehash
        from PIL import Image

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        phash = str(imagehash.phash(image))
        result["phash"] = phash
        duplicates = repo.find_duplicate_photos(phash)
        result["duplicate_of"] = duplicates[0] if duplicates else None
        ok_enc, buffer = cv2.imencode(".jpg", frame)
        if ok_enc:
            result["frame_jpeg"] = buffer.tobytes()

    return result


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


# Keywords that betray an AI image generator in a file's metadata / text chunks.
_AI_METADATA_MARKERS = (
    "dall", "stable diffusion", "sdxl", "midjourney", "firefly", "comfyui",
    "automatic1111", "invokeai", "diffusion", "gan", "flux", "imagen",
)
# Provenance (C2PA "Content Credentials") markers worth surfacing to a human.
_PROVENANCE_MARKERS = (b"c2pa", b"contentcredentials", b"jumbf")

_SYNTHETIC_VISION_PROMPT = (
    "You are a forensic media analyst reviewing a photo submitted as insurance "
    "damage evidence. Decide whether it is a real photograph of a real vehicle or "
    "AI-generated / digitally manipulated. Look for: warped or garbled text and "
    "number plates, inconsistent shadows or reflections, melted or blended edges, "
    "impossible geometry, unnatural repeating textures, or missing/extra parts. "
    'Respond ONLY with JSON: {"verdict": "real|suspicious|likely_ai", '
    '"confidence": 0-100, "reasons": ["..."]}'
)


def detect_synthetic_media(
    filename: str, data: bytes, mime: str = "image/jpeg"
) -> dict[str, Any] | None:
    """Screen an image (or a video frame) for signs of being AI-generated.

    Combines cheap, explainable metadata forensics with a vision-model artifact
    check. This is a *risk indicator* for a human investigator, not a definitive
    verdict. Returns a fraud-style signal dict, or None if nothing looks off.
    """
    reasons: list[str] = []
    severity = "low"

    # --- Metadata forensics (deterministic, offline) -----------------------
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        image = Image.open(io.BytesIO(data))
        exif = {TAGS.get(tid, tid): val for tid, val in image.getexif().items()}

        has_camera = bool(exif.get("Make") or exif.get("Model"))
        if not has_camera:
            reasons.append("no camera make/model in metadata (real photos usually have it)")

        # Scan EXIF software fields and any embedded text chunks (PNG etc.).
        haystack_parts = [
            str(exif.get("Software", "")),
            str(exif.get("ProcessingSoftware", "")),
            " ".join(f"{k}:{v}" for k, v in getattr(image, "info", {}).items()),
            " ".join(getattr(image, "text", {}).keys()) if hasattr(image, "text") else "",
        ]
        haystack = " ".join(haystack_parts).lower()
        for marker in _AI_METADATA_MARKERS:
            if marker in haystack:
                reasons.append(f"metadata references an AI generator ('{marker}')")
                severity = "high"
                break
        if ("parameters" in haystack or "prompt" in haystack) and severity != "high":
            reasons.append("metadata contains generation parameters/prompt text")
            severity = "high"
    except Exception:
        pass

    # Best-effort byte scan for C2PA / Content Credentials provenance markers.
    low_bytes = data[:200_000].lower()
    if any(marker in low_bytes for marker in _PROVENANCE_MARKERS):
        reasons.append("embedded content-provenance (C2PA) data present — verify origin")
        if severity == "low":
            severity = "medium"

    # --- Vision-model artifact check ---------------------------------------
    try:
        from insurclaim.llm import call_vision, extract_json

        raw = call_vision(_SYNTHETIC_VISION_PROMPT, data, mime=mime)
        verdict = extract_json(raw or "") or {}
        v = str(verdict.get("verdict", "")).lower()
        conf = verdict.get("confidence")
        vreasons = verdict.get("reasons") or []
        if v == "likely_ai":
            severity = "high"
            reasons.append(
                f"vision model: likely AI-generated"
                + (f" (confidence {conf})" if conf is not None else "")
            )
            reasons.extend(str(r) for r in vreasons[:2])
        elif v == "suspicious":
            if severity != "high":
                severity = "medium"
            reasons.append(
                "vision model: suspicious"
                + (f" (confidence {conf})" if conf is not None else "")
            )
            reasons.extend(str(r) for r in vreasons[:2])
    except Exception:
        pass

    # "No camera metadata" on its own is too weak to raise an alarm (ordinary
    # re-saved photos / screenshots also lack EXIF), so only surface a signal once
    # something stronger fired (generator tag, provenance data, or a vision
    # verdict) — i.e. medium or high severity.
    if not reasons or severity == "low":
        return None
    return {
        "code": "synthetic_media_risk",
        "message": f"'{filename}' shows signs of being AI-generated / manipulated",
        "evidence": "; ".join(reasons),
        "severity": severity,
    }


def build_claim_text(documents: list[tuple[str, bytes]], media: list[dict]) -> str:
    """Combine extracted document text and photo/video notes into one narrative."""
    parts = [extract_text(name, data) for name, data in documents]
    for item in media:
        kind = item.get("kind", "photo")
        note = f"[{kind} {item['file_name']}]"
        if item.get("duration_s"):
            note += f" ({item['duration_s']:.0f}s)"
        if item.get("duplicate_of"):
            note += " (WARNING: matches media already on another claim)"
        if item.get("damage"):
            note += f" damage: {item['damage']}"
        synthetic = item.get("synthetic")
        if synthetic:
            note += f" SYNTHETIC-MEDIA WARNING: {synthetic.get('evidence', '')}"
        parts.append(note)
    return "\n\n".join(p for p in parts if p)
