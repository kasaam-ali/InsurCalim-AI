import { useEffect, useState } from "react";
import { fetchModel } from "../api.js";
import { SectionHeader, Card, Loading, ErrorNote, Bar } from "../components/ui.jsx";

export default function ModelSection() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchModel().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote>{error}</ErrorNote>;
  if (!data) return <Loading label="Loading model card…" />;

  const maxImp = Math.max(1e-6, ...data.features.map((f) => f.importance));

  return (
    <div>
      <SectionHeader eyebrow="Machine learning" title="Model performance"
                     subtitle="Tabular classifier on a real 30k-row dataset + a narrative classifier fine-tuned on claim text." />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {data.metrics.map((m) => (
          <Card key={m.label}>
            <div className="text-xs font-medium uppercase tracking-wide text-muted">{m.label}</div>
            <div className="tnum mt-1 font-mono text-3xl font-bold text-primary">{m.value}</div>
            <div className="mt-1 text-xs text-muted">{m.note}</div>
          </Card>
        ))}
      </div>

      <Card className="mt-6">
        <h3 className="mb-4 font-semibold">Top fraud signals the model learned</h3>
        {data.features.length === 0 ? (
          <p className="text-sm text-muted">
            {data.features_error
              ? `Model not available: ${data.features_error}`
              : "Tabular model not trained yet."}
          </p>
        ) : (
          <div className="space-y-4">
            {data.features.map((f) => (
              <Bar key={f.name} label={f.name} value={Math.round(f.importance * 100)} max={Math.round(maxImp * 100)}
                   tone="#7C3AED" suffix="%" />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
