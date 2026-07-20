"""Run a full claim investigation and report progress step by step.

This is a faithful extraction of the orchestration in ``frontend/app.py``'s
``page_submit`` — the same calls, in the same order — refactored so it can be
driven from the HTTP API and emit live progress through an ``on_step`` callback
instead of Streamlit's ``st.write`` / ``st.status``.

No investigation, ML, or database logic lives here; it only sequences the
existing modules and shapes a JSON-serialisable result for the React client.
"""

from __future__ import annotations

import base64
from typing import Any, Callable

# Progress callback: receives (step_key, human_message).
StepFn = Callable[[str, str], None]


def _noop(_step: str, _message: str) -> None:  # pragma: no cover - default sink
    pass


def _json_safe_media(info: dict[str, Any]) -> dict[str, Any]:
    """Drop/encode non-serialisable bytes so a media dict can go over JSON.

    Video frames come back as raw JPEG bytes (``frame_jpeg``); expose them as a
    base64 data URL the browser can render, and keep only display-safe fields.
    """
    safe = {k: v for k, v in info.items() if not isinstance(v, (bytes, bytearray))}
    frame = info.get("frame_jpeg")
    if isinstance(frame, (bytes, bytearray)):
        safe["frame_data_url"] = "data:image/jpeg;base64," + base64.b64encode(frame).decode()
    return safe


def run_investigation(
    files: list[tuple[str, bytes]],
    text: str = "",
    doc_ids: list[int] | None = None,
    on_step: StepFn = _noop,
) -> dict[str, Any]:
    """Investigate one claim end-to-end and return the full result payload.

    ``files`` is a list of ``(filename, data)`` uploads (documents, photos,
    videos). ``text`` is optional pasted claim text. ``doc_ids`` selects which
    uploaded policies to check coverage against (``None`` = all). ``on_step`` is
    called before each stage with a short key and a plain-English message so the
    caller can stream live progress.

    The returned dict mirrors the Streamlit ``last_submission`` shape:
    ``documents, coverage, amount, final, media, notices, degraded`` (+ ``text``).
    """
    from insurclaim import intake_docs
    from insurclaim import coverage as cov_mod
    from insurclaim.graph import run_claim
    from insurclaim import amount as amount_mod

    doc_tuples: list[tuple[str, bytes]] = []
    media_infos: list[dict[str, Any]] = []
    n_docs = n_img = n_vid = 0

    on_step("read", "Reading the files you uploaded…")
    for name, data in files:
        kind = intake_docs.classify_upload(name)
        if kind == "document":
            on_step("read", f"Reading the text inside {name}…")
            doc_tuples.append((name, data))
            n_docs += 1
        elif kind == "image":
            on_step("photo_reuse", f"Checking whether photo {name} was reused from another claim…")
            info = intake_docs.process_photo(name, data)
            info["kind"] = "photo"
            on_step("vision", f"Looking at {name} to see the damage and whether the photo is AI-generated…")
            info["damage"] = intake_docs.analyze_damage(data)
            info["synthetic"] = intake_docs.detect_synthetic_media(name, data)
            media_infos.append(info)
            n_img += 1
        elif kind == "video":
            on_step("video", f"Taking a still picture from the video {name}…")
            info = intake_docs.process_video(name, data)
            frame = info.get("frame_jpeg")
            if frame:
                on_step("vision", f"Looking at the video from {name} for damage and signs of fakery…")
                info["damage"] = intake_docs.analyze_damage(frame)
                info["synthetic"] = intake_docs.detect_synthetic_media(name, frame)
            media_infos.append(info)
            n_vid += 1
        # Unsupported types are silently ignored (matches the uploader's allow-list).

    claim_text = intake_docs.build_claim_text(doc_tuples, media_infos)
    if text.strip():
        claim_text = (text.strip() + "\n\n" + claim_text).strip()
    if not claim_text:
        raise ValueError("Provide at least one document, photo, video, or some text.")

    # User-facing notices, re-shown when the stored result is re-rendered.
    notices: list[dict[str, str]] = [
        {"level": "success",
         "message": f"Ingested {n_docs} document(s) · {n_img} photo(s) · {n_vid} video(s)."}
    ]
    for info in media_infos:
        label = str(info.get("kind", "media")).capitalize()
        if info.get("duplicate_of"):
            notices.append({
                "level": "error",
                "message": (f"⚠ {label} {info['file_name']} matches media already on claim "
                            f"#{info['duplicate_of']['claim_id']} — possible reuse."),
            })
        syn = info.get("synthetic")
        if syn:
            notices.append({
                "level": "error",
                "message": (f"🧪 AI-generated media suspected · {info['file_name']} "
                            f"({syn['severity']}): {syn['evidence']}"),
            })

    # 1) Policy gate first: coverage + required-document completeness.
    documents = coverage_result = None
    on_step("coverage", "Checking whether the policy covers this claim, and which documents are missing…")
    try:
        documents = cov_mod.check_documents(claim_text, doc_ids=doc_ids or None)
    except Exception:
        documents = None
    try:
        coverage_result = cov_mod.check_coverage(claim_text, doc_ids=doc_ids or None)
        if (coverage_result.get("decision") == "needs_review"
                and not coverage_result.get("citations")):
            coverage_result = None  # no policies on file - skip the block
    except Exception:
        coverage_result = None
    if documents and documents.get("missing"):
        notices.append({
            "level": "warning",
            "message": "📄 Missing documents: " + ", ".join(str(d) for d in documents["missing"]),
        })

    # 2) The fraud pipeline (plain-language step messages, no agent jargon).
    on_step("understand", "Understanding the claim and pulling out the key facts…")
    on_step("rebuild", "Rebuilding what happened and checking the story for fraud…")
    on_step("write", "Writing up the findings into an investigator report…")
    final = run_claim({"raw_documents": claim_text})

    # 3) Fair-amount estimate (useful even when the claim is not fraud).
    amount_assessment = None
    on_step("amount", "Working out a fair repair cost from today's market prices…")
    try:
        claimed = (final.get("extracted") or {}).get("claimed_amount")
        amount_assessment = amount_mod.assess_amount(
            claim_text, claimed_amount=claimed, doc_ids=doc_ids or None
        )
    except Exception:
        amount_assessment = None

    # Claimant-level overview (profile, summary, parties, documents, risk snapshot).
    overview = None
    try:
        from insurclaim import overview as overview_mod

        overview = overview_mod.build_overview(
            final.get("extracted"), final.get("report"), documents
        )
    except Exception:
        overview = None

    return {
        "ref": "uploaded claim",
        "text": claim_text,
        "doc_ids": doc_ids or None,
        "documents": documents,
        "coverage": coverage_result,
        "amount": amount_assessment,
        "final": final,
        "overview": overview,
        "notices": notices,
        "media": [_json_safe_media(m) for m in media_infos],
        "degraded": bool((final.get("extracted") or {}).get("_extraction_degraded")),
    }
