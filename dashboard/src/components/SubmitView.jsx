import { useRef, useState } from "react";
import { UploadCloud, FileText, Image as ImageIcon, Film, X, ShieldCheck } from "lucide-react";
import { Card } from "./ui.jsx";

const ACCEPT = ".txt,.pdf,.docx,.jpg,.jpeg,.png,.mp4,.mov,.avi,.mkv,.webm";

function iconFor(name) {
  const ext = name.split(".").pop().toLowerCase();
  if (["jpg", "jpeg", "png"].includes(ext)) return ImageIcon;
  if (["mp4", "mov", "avi", "mkv", "webm"].includes(ext)) return Film;
  return FileText;
}

export default function SubmitView({ policies = [], onSubmit }) {
  const [files, setFiles] = useState([]);
  const [text, setText] = useState("");
  const [docIds, setDocIds] = useState([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  function addFiles(list) {
    const incoming = Array.from(list || []);
    setFiles((prev) => {
      const seen = new Set(prev.map((f) => f.name + f.size));
      return [...prev, ...incoming.filter((f) => !seen.has(f.name + f.size))];
    });
  }
  const removeFile = (idx) => setFiles((prev) => prev.filter((_, i) => i !== idx));
  const togglePolicy = (id) =>
    setDocIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  // With no files the pasted text is the whole claim, so a stray word like "hi"
  // must not reach the pipeline. The server applies the authoritative check.
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  const textTooThin = files.length === 0 && text.trim().length > 0 && words < 8;
  const canSubmit = (files.length > 0 || text.trim().length > 0) && !textTooThin;

  return (
    <div className="mx-auto max-w-3xl">
      <Card>
        <h2 className="text-lg font-bold">Submit a claim to investigate</h2>
        <p className="mt-1 text-sm text-muted">
          Upload the claim narrative, police report / FIR (txt · pdf · docx), damage photos and
          dashcam video. The system extracts the data, checks media for reuse and deepfakes, then
          runs the full investigation.
        </p>

        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
          className={`mt-5 cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition ${
            dragging ? "border-primary bg-primary-soft" : "border-line hover:border-primary/50 hover:bg-bg"
          }`}
        >
          <UploadCloud className="mx-auto h-8 w-8 text-primary" />
          <div className="mt-2 text-sm font-medium">Drop files here, or click to browse</div>
          <div className="mt-1 text-xs text-muted">Documents · photos · videos</div>
          <input ref={inputRef} type="file" multiple accept={ACCEPT} className="hidden"
                 onChange={(e) => addFiles(e.target.files)} />
        </div>

        {files.length > 0 && (
          <ul className="mt-3 space-y-2">
            {files.map((f, i) => {
              const Icon = iconFor(f.name);
              return (
                <li key={f.name + i} className="flex items-center gap-3 rounded-lg border border-line bg-bg px-3 py-2">
                  <Icon className="h-4 w-4 shrink-0 text-primary" />
                  <span className="truncate text-sm">{f.name}</span>
                  <span className="tnum ml-auto text-xs text-muted">{(f.size / 1024).toFixed(0)} KB</span>
                  <button onClick={() => removeFile(i)} className="rounded-md p-1 text-muted hover:bg-line hover:text-ink"
                          aria-label={`Remove ${f.name}`}>
                    <X className="h-4 w-4" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}

        <label className="mt-5 block text-sm font-medium">Or paste claim text</label>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4}
                  placeholder="e.g. 2019 Toyota Corolla rear-ended in Lahore; boot lid and rear bumper damaged. Claimant demands PKR 300,000."
                  className="field mt-2" />
        {textTooThin && (
          <p className="mt-2 text-xs text-warn">
            Please describe the claim properly: the vehicle, what happened, the damage and the
            amount being claimed. A few words are not enough to investigate.
          </p>
        )}

        <div className="mt-5">
          <div className="flex items-center gap-2 text-sm font-medium">
            <ShieldCheck className="h-4 w-4 text-primary" /> Check against which policy?
          </div>
          {policies.length === 0 ? (
            <p className="mt-2 text-xs text-muted">No policies on file checked against all uploaded policies.</p>
          ) : (
            <div className="mt-2 flex flex-wrap gap-2">
              {policies.map((p) => {
                const on = docIds.includes(p.id);
                return (
                  <button key={p.id} onClick={() => togglePolicy(p.id)}
                          className={`rounded-full border px-3 py-1.5 text-xs transition ${
                            on ? "border-primary bg-primary-soft text-primary" : "border-line text-muted hover:border-primary/40 hover:text-ink"
                          }`}>
                    #{p.id} · {p.company} · {p.doc_name}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <button className="btn-primary mt-6 w-full sm:w-auto" disabled={!canSubmit}
                onClick={() => onSubmit({ files, text: text.trim(), docIds })}>
          Process & investigate
        </button>
      </Card>
    </div>
  );
}
