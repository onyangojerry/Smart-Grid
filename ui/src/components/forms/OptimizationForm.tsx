import React, { useState } from "react";
import type { OptimizationRunBody } from "../../types";

type Props = {
  onSubmit: (body: OptimizationRunBody) => void;
  loading?: boolean;
};

export function OptimizationForm({ onSubmit, loading }: Props) {
  const [mode, setMode] = useState<"live" | "simulation" | "backtest">("live");
  const [horizon, setHorizon] = useState(60);
  const [step, setStep] = useState(5);
  const [allowExport, setAllowExport] = useState(true);
  const [reserveSocMin, setReserveSocMin] = useState(20);

  return (
    <form
      className="auth-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          mode,
          horizon_minutes: horizon,
          step_minutes: step,
          allow_export: allowExport,
          reserve_soc_min: reserveSocMin
        });
      }}
      style={{ maxWidth: 800 }}
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        <div className="form-group">
          <label className="form-label">Mode</label>
          <select className="form-input" value={mode} onChange={(e) => setMode(e.target.value as "live" | "simulation" | "backtest")}>
            <option value="live">Live Execution</option>
            <option value="simulation">Simulation</option>
            <option value="backtest">Backtest</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Horizon (Minutes)</label>
          <input className="form-input" type="number" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} />
        </div>
        <div className="form-group">
          <label className="form-label">Step (Minutes)</label>
          <input className="form-input" type="number" value={step} onChange={(e) => setStep(Number(e.target.value))} />
        </div>
        <div className="form-group">
          <label className="form-label">Reserve SOC (%)</label>
          <input className="form-input" type="number" value={reserveSocMin} onChange={(e) => setReserveSocMin(Number(e.target.value))} />
        </div>
        <div className="form-group" style={{ display: "flex", alignItems: "center", paddingTop: 24 }}>
          <label style={{ display: "flex", gap: 12, alignItems: "center", cursor: "pointer", fontWeight: 600 }}>
            <input type="checkbox" style={{ width: 20, height: 20 }} checked={allowExport} onChange={(e) => setAllowExport(e.target.checked)} />
            Allow Export
          </label>
        </div>
      </div>
      <button className="btn btn-primary btn-lg" disabled={loading} type="submit" style={{ marginTop: 16 }}>
        {loading ? "Running..." : "Execute Smart Logic"}
      </button>
    </form>
  );
}
