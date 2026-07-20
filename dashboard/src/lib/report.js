// Deterministic report helpers ported from the Streamlit app (frontend/app.py):
// risk banding, two-line truncation, and the plain-English summary. No LLM calls
// — everything is derived from fields already in the report, so it is instant.

export function riskMeta(score) {
  const s = Number(score) || 0;
  if (s >= 60) return { label: "HIGH", tone: "bad" };
  if (s >= 30) return { label: "MEDIUM", tone: "warn" };
  return { label: "LOW", tone: "good" };
}

// Semantic risk colours (light theme).
export const TONE_HEX = {
  good: "#16A34A",
  warn: "#D97706",
  bad: "#DC2626",
};

export const BAND_TONE = { HIGH: "bad", MEDIUM: "warn", LOW: "good" };

// Word-boundary truncation to roughly two lines.
export function twoLine(text, maxChars = 180) {
  const t = (text || "").trim().replace(/\s+/g, " ");
  if (t.length <= maxChars) return t;
  const cut = t.slice(0, maxChars);
  const lastSpace = cut.lastIndexOf(" ");
  return (lastSpace > 0 ? cut.slice(0, lastSpace) : cut) + "…";
}

const ACTION_PHRASING = {
  route_to_investigator: "should be routed to a human investigator",
  request_more_info: "needs more information before a decision",
  fast_track_approve: "looks straightforward enough to fast-track",
};

// A 2-4 sentence plain-English summary composed from report + amount fields.
export function plainSummary(report, amount) {
  const score = Math.round(Number(report?.risk_score) || 0);
  const { label } = riskMeta(score);
  const action = ACTION_PHRASING[report?.recommended_action] || "needs a human review";
  const flags = (report?.top_flags || []).filter((f) => f?.summary);

  const parts = [];
  parts.push(
    `This claim scores ${score}/100 on risk (${label.toLowerCase()}), so it ${action}.`
  );

  if (flags.length === 1) {
    parts.push(`One thing stands out: ${lower(flags[0].summary)}.`);
  } else if (flags.length > 1) {
    parts.push(
      `${flags.length} things stand out — starting with ${lower(flags[0].summary)}.`
    );
  } else {
    parts.push("No specific red flags surfaced from the documents and media.");
  }

  if (amount && amount.verdict) {
    const v = amount.verdict;
    if (v === "overstated") {
      parts.push("The demanded amount also looks overstated versus a fair market repair cost.");
    } else if (v === "fair" || v === "reasonable") {
      parts.push("The demanded amount looks broadly fair against market repair costs.");
    } else if (v === "understated") {
      parts.push("The demanded amount is actually below the fair market repair cost.");
    }
  }

  parts.push("Nothing is auto-decided — a human adjuster makes the final call.");
  return parts.join(" ");
}

function lower(s) {
  const t = (s || "").trim();
  return t ? t[0].toLowerCase() + t.slice(1) : t;
}

export function fmtMoney(value, currency = "PKR") {
  if (value === null || value === undefined || value === "") return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  return `${currency} ${n.toLocaleString("en-PK")}`;
}
