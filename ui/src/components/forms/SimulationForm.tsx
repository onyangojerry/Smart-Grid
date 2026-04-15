import React, { useState } from "react";
import type { SimulationRunBody } from "../../types";

type Props = {
  onSubmit: (body: SimulationRunBody) => void;
  loading?: boolean;
};

export function SimulationForm({ onSubmit, loading }: Props) {
  const [mode, setMode] = useState<"simulation" | "backtest">("simulation");
  const [stepMinutes, setStepMinutes] = useState(5);
  const [allowExport, setAllowExport] = useState(true);
  const [reserveSocMin, setReserveSocMin] = useState(20);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ mode, step_minutes: stepMinutes, allow_export: allowExport, reserve_soc_min: reserveSocMin });
      }}
      className="auth-form"
      style={{ maxWidth: 600 }}
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div className="form-group">
          <label className="form-label">Simulation Mode</label>
          <select className="form-input" value={mode} onChange={(e) => setMode(e.target.value as "simulation" | "backtest")}>
            <option value="simulation">Simulation</option>
            <option value="backtest">Backtest</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Step (Minutes)</label>
          <input className="form-input" type="number" value={stepMinutes} onChange={(e) => setStepMinutes(Number(e.target.value))} />
        </div>
        <div className="form-group">
          <label className="form-label">Reserve SOC (%)</label>
          <input className="form-input" type="number" value={reserveSocMin} onChange={(e) => setReserveSocMin(Number(e.target.value))} />
        </div>
        <div className="form-group" style={{ display: "flex", alignItems: "center", paddingTop: 24 }}>
          <label style={{ display: "flex", gap: 12, alignItems: "center", cursor: "pointer", fontWeight: 600 }}>
            <input type="checkbox" style={{ width: 20, height: 20 }} checked={allowExport} onChange={(e) => setAllowExport(e.target.checked)} />
            Allow Grid Export
          </label>
        </div>
      </div>
      <button className="btn btn-primary btn-lg" disabled={loading} type="submit" style={{ marginTop: 16 }}>
        {loading ? "Running..." : "Start Future Simulation"}
      </button>
    </form>
  );
}
