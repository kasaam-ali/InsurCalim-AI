import { UserSquare } from "lucide-react";
import { SectionHeader, Card, StatCard } from "../components/ui.jsx";
import { fmtMoney } from "../lib/report.js";
import RiskGauge from "../components/RiskGauge.jsx";

// Consolidated claimant overview, built from the most recent investigation's
// `overview` payload (insurclaim.overview.build_overview).
export default function ClaimantSection({ result, onGoSubmit }) {
  const ov = result?.overview;

  if (!ov) {
    return (
      <div>
        <SectionHeader eyebrow="Investigate" title="Claimant overview" />
        <Card className="text-center">
          <UserSquare className="mx-auto h-10 w-10 text-muted" />
          <p className="mt-3 text-sm text-muted">
            Submit a claim first — the consolidated claimant overview will appear here.
          </p>
          <button className="btn-primary mx-auto mt-4" onClick={onGoSubmit}>Go to Submit a claim</button>
        </Card>
      </div>
    );
  }

  const ccy = result?.amount?.currency || "PKR";
  const docs = ov.documents || {};
  const presentN = (docs.present || []).length;
  const requiredN = (docs.required || []).length;

  return (
    <div>
      <SectionHeader eyebrow="Investigate" title={ov.claimant || "Claimant overview"}
                     subtitle="Consolidated overview of this claimant and their claim." />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Incident date" value={ov.incident_date || "—"} />
        <StatCard label="Location" value={ov.location || "—"} />
        <StatCard label="Vehicle" value={ov.vehicle || "—"} />
        <StatCard label="Demanded amount" value={fmtMoney(ov.claimed_amount, ccy)} tone="#D97706" />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_300px]">
        <div className="space-y-4">
          {ov.summary && (
            <Card>
              <h3 className="mb-2 font-semibold">Claim summary</h3>
              <p className="text-sm leading-relaxed text-ink-soft">{ov.summary}</p>
            </Card>
          )}

          {ov.parties?.length > 0 && (
            <Card>
              <h3 className="mb-2 font-semibold">Parties</h3>
              <ul className="space-y-1 text-sm">
                {ov.parties.map((p, i) => (
                  <li key={i}><span className="font-medium">{p.full_name}</span>
                    <span className="text-muted"> — {p.role}</span></li>
                ))}
              </ul>
            </Card>
          )}

          {docs && (docs.required || docs.missing || docs.present) && (
            <Card>
              <h3 className="mb-2 font-semibold">Documents checklist
                <span className="ml-2 text-xs font-normal text-muted">{presentN}/{requiredN || presentN} present</span>
              </h3>
              {docs.present?.length > 0 && (
                <p className="text-sm text-good">✓ Present: {docs.present.join(", ")}</p>
              )}
              {docs.missing?.length > 0 && (
                <p className="mt-1 text-sm text-bad">✗ Missing: {docs.missing.join(", ")}</p>
              )}
              {(docs.incomplete || []).map((inc, i) => (
                <p key={i} className="mt-1 text-sm text-warn">
                  ⚠ Incomplete: {typeof inc === "object" ? `${inc.document || ""} — ${inc.issue || ""}` : inc}
                </p>
              ))}
            </Card>
          )}
        </div>

        <Card className="flex flex-col items-center text-center">
          <h3 className="mb-2 self-start font-semibold">Risk snapshot</h3>
          <RiskGauge score={ov.risk_score} />
          <div className="mt-2 text-xs text-muted">
            Recommended: <span className="text-ink">{ov.recommended_action}</span>
          </div>
        </Card>
      </div>
    </div>
  );
}
