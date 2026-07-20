"""Starlette HTTP API for the InsurCalim AI React dashboard.

Built on Starlette (already a dependency via Streamlit) rather than FastAPI, so
it adds no new packages and cannot clash with the pinned Starlette version.

Endpoints (all require the shared demo token — Bearer header or ``?token=``):
  GET  /api/health                       liveness probe (no auth)
  GET  /api/policies                     uploaded policies for the coverage picker
  POST /api/investigate                  start a job (multipart: files, text, doc_ids)
  GET  /api/investigate/{job_id}/events  Server-Sent Events: live steps + final result
  GET  /api/investigate/{job_id}/pdf     the investigator report as a PDF

Run: .venv/Scripts/python.exe -m uvicorn api.main:app --port 8000
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route

from api.pipeline import run_investigation


class SafeJSON(JSONResponse):
    """JSON response that tolerates datetimes and other non-native types."""

    def render(self, content: Any) -> bytes:
        return json.dumps(content, default=str, ensure_ascii=False).encode("utf-8")


# Same shared demo token the Streamlit gate checks (frontend/app.py).
TOKEN = os.getenv("APP_LOGIN_TOKEN", "insurclaim-demo-2026")

# In-memory job registry. Fine for a single-process demo server.
JOBS: dict[str, dict[str, Any]] = {}


# --------------------------------------------------------------------------- #
# Auth helpers
# --------------------------------------------------------------------------- #
def _token_from(request: Request) -> str | None:
    """Read the token from the Authorization: Bearer header or a ?token= query."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.query_params.get("token")


def _unauthorized(request: Request) -> JSONResponse | None:
    """Return a 401 response if the request is not authenticated, else None."""
    if not TOKEN or _token_from(request) != TOKEN:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return None


def _sse(data: Any, event: str | None = None) -> str:
    """Format a Server-Sent Events frame."""
    prefix = f"event: {event}\n" if event else ""
    return prefix + "data: " + json.dumps(data, default=str) + "\n\n"


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def policies(request: Request) -> JSONResponse:
    if (guard := _unauthorized(request)) is not None:
        return guard
    from insurclaim.db import repo

    loop = asyncio.get_running_loop()
    rows = await loop.run_in_executor(None, repo.list_policy_documents)
    return SafeJSON(rows)


async def claims(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    from api import scoring

    loop = asyncio.get_running_loop()
    rows = await loop.run_in_executor(None, scoring.claims_list)
    return SafeJSON(rows)


async def stats(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    from api import scoring

    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, scoring.portfolio_stats)
    return SafeJSON(data)


async def analytics(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    from api import scoring

    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, scoring.analytics)
    return SafeJSON(data)


async def rings(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    from api import scoring

    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, scoring.fraud_rings)
    return SafeJSON(data)


async def claim_detail(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    from api import scoring

    try:
        claim_id = int(request.path_params["claim_id"])
    except (TypeError, ValueError):
        return JSONResponse({"error": "bad claim id"}, status_code=400)
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, scoring.claim_detail, claim_id)
    if data is None:
        return JSONResponse({"error": "unknown claim"}, status_code=404)
    return SafeJSON(data)


async def model_card(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard

    def build() -> dict[str, Any]:
        # Static headline metrics (from the tabular + narrative evaluation).
        card: dict[str, Any] = {
            "metrics": [
                {"label": "Tabular ROC-AUC", "value": "0.74", "note": "real held-out set"},
                {"label": "Fraud recall", "value": "67%", "note": "@ threshold 0.25"},
                {"label": "Narrative recall", "value": "high", "note": "fine-tuned on claim text"},
            ],
            "features": [],
        }
        try:
            import joblib
            from insurclaim.ml.train_tabular import MODEL_PATH

            if MODEL_PATH.exists():
                model = joblib.load(MODEL_PATH)
                names = model.named_steps["preprocess"].get_feature_names_out()
                importances = model.named_steps["classifier"].feature_importances_
                top = sorted(zip(names, importances), key=lambda x: -x[1])[:10]
                card["features"] = [
                    {"name": str(n).split("__")[-1][:26], "importance": round(float(v), 4)}
                    for n, v in top
                ]
        except Exception as exc:
            card["features_error"] = str(exc)
        return card

    loop = asyncio.get_running_loop()
    return SafeJSON(await loop.run_in_executor(None, build))


async def add_policy(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    form = await request.form()
    company = str(form.get("company") or "").strip() or "DemoInsure"
    doc_name = str(form.get("doc_name") or "").strip() or "policy"
    content = str(form.get("text") or "").strip()

    upload = form.get("file")
    file_bytes = file_name = None
    if hasattr(upload, "read"):
        file_bytes = await upload.read()
        file_name = upload.filename or "policy.txt"

    def work() -> dict[str, Any]:
        from insurclaim import coverage, intake_docs
        from api import scoring

        body = content
        if not body and file_bytes:
            body = intake_docs.extract_text(file_name, file_bytes)
        if not body:
            return {"error": "no policy text extracted"}
        doc_id = coverage.add_policy_document(company, doc_name, body)
        scoring.invalidate()
        return {"id": doc_id}

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, work)
    status = 400 if result.get("error") else 200
    return SafeJSON(result, status_code=status)


async def delete_policy(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    try:
        doc_id = int(request.path_params["doc_id"])
    except (TypeError, ValueError):
        return JSONResponse({"error": "bad id"}, status_code=400)

    def work() -> None:
        from insurclaim import coverage
        from api import scoring

        coverage.remove_policy_document(doc_id)
        scoring.invalidate()

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, work)
    return SafeJSON({"ok": True})


async def check_coverage(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    payload = await request.json()
    text = str(payload.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "no claim text"}, status_code=400)

    def work() -> dict[str, Any]:
        from insurclaim import coverage

        return coverage.check_coverage(text)

    loop = asyncio.get_running_loop()
    return SafeJSON(await loop.run_in_executor(None, work))


async def get_case(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    ref = request.path_params["ref"]

    def work() -> dict[str, Any]:
        from insurclaim.db import repo

        return {
            "status": repo.get_case_status(ref) or {},
            "notes": repo.list_case_notes(ref),
        }

    loop = asyncio.get_running_loop()
    return SafeJSON(await loop.run_in_executor(None, work))


async def set_case(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    ref = request.path_params["ref"]
    payload = await request.json()
    status = str(payload.get("status") or "open")
    assignee = payload.get("assignee")

    def work() -> None:
        from insurclaim.db import repo

        repo.set_case_status(ref, status, assignee)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, work)
    return SafeJSON({"ok": True})


async def add_case_note(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    ref = request.path_params["ref"]
    payload = await request.json()
    note = str(payload.get("note") or "").strip()
    if not note:
        return JSONResponse({"error": "empty note"}, status_code=400)

    def work() -> list[dict[str, Any]]:
        from insurclaim.db import repo

        repo.add_case_note(ref, note)
        return repo.list_case_notes(ref)

    loop = asyncio.get_running_loop()
    return SafeJSON(await loop.run_in_executor(None, work))


CHAT_SYSTEM = (
    "You are InsurCalim AI, an assistant for an auto-insurance fraud investigator, embedded in "
    "the InsurCalim investigator dashboard. Answer clearly and concisely.\n\n"
    "How InsurCalim works (use this to answer accurately):\n"
    "- Risk score (0-100) = deterministic rules + duplicate-photo (perceptual hash) checks + "
    "similar-claim retrieval (RAG over past claims) + a narrative ML classifier (DistilBERT) and "
    "a tabular Random-Forest fraud probability. Bands: HIGH >= 60, MEDIUM 30-59, LOW < 30.\n"
    "- Each flag carries evidence; 'reason codes' show how much each signal added to the score.\n"
    "- Fraud rings = groups of claims linked by high RAG similarity to known-fraud claims.\n"
    "- The fair-cost estimate prices the damage from live market prices in PKR and flags "
    "over-stated demands; it is an estimate to guide a human, not a final settlement.\n"
    "- The system only flags, ranks and explains. It NEVER auto-approves or auto-denies; a human "
    "adjuster always makes the final decision. Data is synthetic / public only.\n\n"
    "If the provided context does not contain a specific figure, say what the investigator should "
    "check next rather than guessing."
)


async def chat(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    payload = await request.json()
    question = str(payload.get("question") or "").strip()
    context = str(payload.get("context") or "").strip()
    if not question:
        return JSONResponse({"error": "empty question"}, status_code=400)

    def work() -> dict[str, Any]:
        from insurclaim.llm import call_llm

        prompt = question if not context else f"Context:\n{context}\n\nQuestion: {question}"
        try:
            answer = call_llm(prompt, system=CHAT_SYSTEM)
        except Exception as exc:
            return {"answer": f"The assistant is unavailable right now ({exc}).", "degraded": True}
        return {"answer": answer}

    loop = asyncio.get_running_loop()
    return SafeJSON(await loop.run_in_executor(None, work))


async def investigate(request: Request) -> JSONResponse:
    if (guard := _unauthorized(request)) is not None:
        return guard

    form = await request.form()
    text = str(form.get("text") or "")
    doc_ids = [int(x) for x in form.getlist("doc_ids") if str(x).strip().isdigit()]

    files: list[tuple[str, bytes]] = []
    for upload in form.getlist("files"):
        if hasattr(upload, "read"):
            data = await upload.read()
            files.append((upload.filename or "upload", data))

    job_id = uuid.uuid4().hex
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    JOBS[job_id] = {"queue": queue, "result": None, "error": None}

    def on_step(step: str, message: str) -> None:
        # Called from the worker thread; hand the event back to the event loop.
        loop.call_soon_threadsafe(
            queue.put_nowait, {"type": "step", "step": step, "message": message}
        )

    def work() -> None:
        try:
            result = run_investigation(files, text, doc_ids or None, on_step)
            JOBS[job_id]["result"] = result
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "done"})
        except Exception as exc:  # surface any failure to the stream
            JOBS[job_id]["error"] = str(exc)
            loop.call_soon_threadsafe(
                queue.put_nowait, {"type": "error", "message": str(exc)}
            )

    loop.run_in_executor(None, work)
    return JSONResponse({"job_id": job_id})


async def events(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    job_id = request.path_params["job_id"]
    job = JOBS.get(job_id)
    if job is None:
        return JSONResponse({"error": "unknown job"}, status_code=404)
    queue: asyncio.Queue = job["queue"]

    async def generator():
        # Nudge proxies/clients to start rendering immediately.
        yield ": stream open\n\n"
        while True:
            item = await queue.get()
            kind = item["type"]
            if kind == "step":
                yield _sse({"step": item["step"], "message": item["message"]}, event="step")
            elif kind == "done":
                yield _sse(job["result"], event="result")
                break
            elif kind == "error":
                yield _sse({"message": item["message"]}, event="error")
                break

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(generator(), media_type="text/event-stream", headers=headers)


async def report_pdf(request: Request) -> Response:
    if (guard := _unauthorized(request)) is not None:
        return guard
    job_id = request.path_params["job_id"]
    job = JOBS.get(job_id)
    if job is None or not job.get("result"):
        return JSONResponse({"error": "no result for this job"}, status_code=404)
    result = job["result"]

    def build() -> bytes:
        from insurclaim import report_builder

        detailed = report_builder.build_detailed(
            result["final"],
            coverage=result.get("coverage"),
            documents=result.get("documents"),
            amount=result.get("amount"),
        )
        return report_builder.to_pdf(detailed, claim_ref="uploaded-claim")

    loop = asyncio.get_running_loop()
    pdf_bytes = await loop.run_in_executor(None, build)
    return Response(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=insurclaim-report.pdf"},
    )


routes = [
    Route("/api/health", health, methods=["GET"]),
    Route("/api/policies", policies, methods=["GET"]),
    Route("/api/policies", add_policy, methods=["POST"]),
    Route("/api/policies/{doc_id}", delete_policy, methods=["DELETE"]),
    Route("/api/coverage/check", check_coverage, methods=["POST"]),
    Route("/api/claims", claims, methods=["GET"]),
    Route("/api/claim/{claim_id}", claim_detail, methods=["GET"]),
    Route("/api/stats", stats, methods=["GET"]),
    Route("/api/analytics", analytics, methods=["GET"]),
    Route("/api/rings", rings, methods=["GET"]),
    Route("/api/model", model_card, methods=["GET"]),
    Route("/api/cases/{ref}", get_case, methods=["GET"]),
    Route("/api/cases/{ref}", set_case, methods=["POST"]),
    Route("/api/cases/{ref}/notes", add_case_note, methods=["POST"]),
    Route("/api/chat", chat, methods=["POST"]),
    Route("/api/investigate", investigate, methods=["POST"]),
    Route("/api/investigate/{job_id}/events", events, methods=["GET"]),
    Route("/api/investigate/{job_id}/pdf", report_pdf, methods=["GET"]),
]

# The dashboard dev server (5174) and the landing page (5173) call this API.
_allowed = os.getenv(
    "DASHBOARD_ORIGINS", "http://localhost:5174,http://localhost:5173"
).split(",")
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _allowed if o.strip()],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
]

app = Starlette(routes=routes, middleware=middleware)
