import React from "react";
import type { ExplanationPayload } from "../../types";
import { Badge } from "../../components/ui/Badge";
import { DataTable } from "../../components/tables/DataTable";

export function ExplanationPanel({ explanation }: { explanation: ExplanationPayload | null | undefined }) {
  if (!explanation) {
    return <div style={{ color: "var(--text-muted)" }}>No explanation available</div>;
  }

  return (
    <div style={{ display: "grid", gap: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Badge kind="plain" value={explanation.decision} />
        <strong style={{ color: "var(--text)" }}>{explanation.target_power_kw.toFixed(1)} kW</strong>
      </div>
      <DataTable
        rows={explanation.top_factors}
        getRowKey={(r) => `${r.factor}-${r.effect}`}
        columns={[
          { key: "factor", header: "factor", render: (r) => r.factor },
          { key: "value", header: "value", render: (r) => r.value },
          { key: "effect", header: "effect", render: (r) => r.effect }
        ]}
      />
      <blockquote style={{ 
        margin: 0, 
        padding: "8px 10px", 
        borderLeft: "4px solid var(--primary)", 
        background: "var(--bg)",
        color: "var(--text)"
      }}>
        {explanation.summary}
      </blockquote>
    </div>
  );
}
