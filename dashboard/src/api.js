// API client for the InsurCalim dashboard.
//
// The token is captured from the sign-in hand-off (?token=…) and reused as a
// Bearer header for fetches and as a query param for the EventSource stream
// (EventSource cannot set headers).

const API_BASE = import.meta.env.VITE_API_URL || "/api";
const TOKEN_KEY = "insurclaim_token";

export function captureToken() {
  const url = new URL(window.location.href);
  const t = url.searchParams.get("token");
  if (t) {
    sessionStorage.setItem(TOKEN_KEY, t);
    url.searchParams.delete("token");
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);
  }
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

function authHeaders(extra = {}) {
  const t = getToken();
  return { ...(t ? { Authorization: `Bearer ${t}` } : {}), ...extra };
}

// Generic request helper. Throws Error("unauthorized") on 401 so the app can
// bounce to the sign-in gate.
async function req(path, { method = "GET", json, form } = {}) {
  const opts = { method, headers: authHeaders() };
  if (json !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(json);
  } else if (form !== undefined) {
    opts.body = form;
  }
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (res.status === 401) throw new Error("unauthorized");
  if (!res.ok) {
    let msg = `request failed (${res.status})`;
    try {
      const b = await res.json();
      if (b.error) msg = b.error;
    } catch (_) {}
    throw new Error(msg);
  }
  return res.status === 204 ? null : res.json();
}

// --- Reads --------------------------------------------------------------- //
export const fetchPolicies = () => req("/policies");
export const fetchClaims = () => req("/claims");
export const fetchStats = () => req("/stats");
export const fetchAnalytics = () => req("/analytics");
export const fetchRings = () => req("/rings");
export const fetchModel = () => req("/model");
export const fetchClaimDetail = (id) => req(`/claim/${id}`);
export const fetchCase = (ref) => req(`/cases/${encodeURIComponent(ref)}`);

// --- Writes -------------------------------------------------------------- //
export const checkCoverage = (text) => req("/coverage/check", { method: "POST", json: { text } });
export const askAssistant = (question, context) => req("/chat", { method: "POST", json: { question, context } });
export const deletePolicy = (id) => req(`/policies/${id}`, { method: "DELETE" });
export const setCase = (ref, status, assignee) =>
  req(`/cases/${encodeURIComponent(ref)}`, { method: "POST", json: { status, assignee } });
export const addCaseNote = (ref, note) =>
  req(`/cases/${encodeURIComponent(ref)}/notes`, { method: "POST", json: { note } });

export function addPolicy({ company, docName, text, file }) {
  const form = new FormData();
  form.append("company", company || "");
  form.append("doc_name", docName || "");
  if (text) form.append("text", text);
  if (file) form.append("file", file, file.name);
  return req("/policies", { method: "POST", form });
}

// Start an investigation; returns the job id.
export async function startInvestigation({ files, text, docIds }) {
  const form = new FormData();
  (files || []).forEach((f) => form.append("files", f, f.name));
  if (text) form.append("text", text);
  (docIds || []).forEach((id) => form.append("doc_ids", String(id)));
  const { job_id } = await req("/investigate", { method: "POST", form });
  return job_id;
}

// Stream live steps for a job. Calls onStep({step, message}) per step, then
// resolves with the final result payload (or rejects on error).
export function streamInvestigation(jobId, onStep) {
  return new Promise((resolve, reject) => {
    const token = getToken();
    const url = `${API_BASE}/investigate/${jobId}/events?token=${encodeURIComponent(token || "")}`;
    const es = new EventSource(url);
    es.addEventListener("step", (e) => {
      try {
        onStep(JSON.parse(e.data));
      } catch (_) {}
    });
    es.addEventListener("result", (e) => {
      es.close();
      resolve(JSON.parse(e.data));
    });
    es.addEventListener("error", (e) => {
      es.close();
      let msg = "The investigation stream was interrupted.";
      if (e && e.data) {
        try {
          msg = JSON.parse(e.data).message || msg;
        } catch (_) {}
      }
      reject(new Error(msg));
    });
  });
}

export function pdfUrl(jobId) {
  const token = getToken();
  return `${API_BASE}/investigate/${jobId}/pdf?token=${encodeURIComponent(token || "")}`;
}

export const LANDING_URL = import.meta.env.VITE_LANDING_URL || "http://localhost:5173";
