import { useEffect, useState } from "react";
import { Trash2, ShieldCheck, Upload } from "lucide-react";
import { fetchPolicies, addPolicy, deletePolicy, checkCoverage } from "../api.js";
import { SectionHeader, Card, Loading, ErrorNote } from "../components/ui.jsx";

const DECISION_TONE = {
  covered: { hex: "#16A34A", label: "COVERED" },
  not_covered: { hex: "#DC2626", label: "NOT COVERED" },
  needs_review: { hex: "#D97706", label: "NEEDS REVIEW" },
};

export default function PolicySection() {
  const [policies, setPolicies] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ company: "DemoInsure", docName: "auto_policy", text: "", file: null });
  const [saving, setSaving] = useState(false);
  const [claimText, setClaimText] = useState("");
  const [coverage, setCoverage] = useState(null);
  const [checking, setChecking] = useState(false);

  function load() {
    fetchPolicies().then(setPolicies).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  async function save() {
    setSaving(true);
    setError("");
    try {
      await addPolicy(form);
      setForm({ ...form, text: "", file: null });
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(id) {
    await deletePolicy(id);
    load();
  }

  async function runCheck() {
    if (!claimText.trim()) return;
    setChecking(true);
    setCoverage(null);
    try {
      setCoverage(await checkCoverage(claimText.trim()));
    } catch (e) {
      setError(e.message);
    } finally {
      setChecking(false);
    }
  }

  return (
    <div>
      <SectionHeader eyebrow="Configure" title="Policy & coverage"
                     subtitle="Upload your policies; incoming claims are checked for whether they're actually covered." />

      {error && <div className="mb-4"><ErrorNote>{error}</ErrorNote></div>}

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Add policy */}
        <Card>
          <h3 className="mb-3 font-semibold">Add a policy</h3>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <input className="field" placeholder="Company" value={form.company}
                     onChange={(e) => setForm({ ...form, company: e.target.value })} />
              <input className="field" placeholder="Document name" value={form.docName}
                     onChange={(e) => setForm({ ...form, docName: e.target.value })} />
            </div>
            <textarea className="field" rows={5} placeholder="Paste policy text (or upload a file below)"
                      value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} />
            <label className="flex cursor-pointer items-center gap-2 text-sm text-muted">
              <Upload className="h-4 w-4" />
              <span>{form.file ? form.file.name : "…or upload txt / pdf / docx"}</span>
              <input type="file" accept=".txt,.pdf,.docx" className="hidden"
                     onChange={(e) => setForm({ ...form, file: e.target.files?.[0] || null })} />
            </label>
            <button className="btn-primary" disabled={saving || (!form.text.trim() && !form.file)} onClick={save}>
              {saving ? "Saving…" : "Save & index policy"}
            </button>
          </div>
        </Card>

        {/* Coverage check */}
        <Card>
          <h3 className="mb-3 font-semibold">Coverage check</h3>
          <textarea className="field" rows={4} placeholder="Paste a claim description to check against your policies…"
                    value={claimText} onChange={(e) => setClaimText(e.target.value)} />
          <button className="btn-primary mt-3" disabled={checking || !claimText.trim()} onClick={runCheck}>
            <ShieldCheck className="h-4 w-4" /> {checking ? "Checking…" : "Check coverage"}
          </button>
          {coverage && (
            <div className="mt-4">
              {(() => {
                const t = DECISION_TONE[coverage.decision] || { hex: "#64748B", label: (coverage.decision || "").toUpperCase() };
                return (
                  <span className="pill" style={{ color: t.hex, background: `${t.hex}16`, border: `1px solid ${t.hex}33` }}>
                    {t.label}
                  </span>
                );
              })()}
              <p className="mt-2 text-sm text-ink-soft">{coverage.rationale}</p>
              {coverage.clause && (
                <p className="mt-2 rounded-lg border-l-2 border-primary bg-primary-soft/60 px-3 py-2 text-xs text-muted">
                  Cited clause: {coverage.clause}
                </p>
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Policies on file */}
      <Card className="mt-4">
        <h3 className="mb-3 font-semibold">Policies on file</h3>
        {!policies ? (
          <Loading label="Loading policies…" />
        ) : policies.length === 0 ? (
          <p className="text-sm text-muted">No policies uploaded yet.</p>
        ) : (
          <ul className="divide-y divide-line">
            {policies.map((p) => (
              <li key={p.id} className="flex items-center gap-3 py-3">
                <span className="tnum font-mono text-sm font-medium">#{p.id}</span>
                <div className="min-w-0">
                  <div className="text-sm font-medium">{p.company} · {p.doc_name}</div>
                  <div className="truncate text-xs text-muted">{p.preview}…</div>
                </div>
                <button onClick={() => remove(p.id)}
                        className="ml-auto rounded-lg p-2 text-muted transition hover:bg-bad-soft hover:text-bad"
                        aria-label={`Remove policy ${p.id}`}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
