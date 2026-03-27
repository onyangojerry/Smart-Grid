import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { calculateROI, createROIScenario, deleteROIScenario, listROIScenarios } from "../../api/roi";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import type { ROIInput, ROIResult } from "../../types";
import "../../styles/features.css";

const defaultInput: ROIInput = {
  name: "New Scenario",
  description: "",
  system: {
    battery_capacity_kwh: 100,
    battery_power_kw: 50,
    solar_capacity_kwp: 50,
    round_trip_efficiency: 0.90
  },
  financial: {
    installation_cost: 50000,
    annual_maintenance_cost: 1000,
    electricity_import_price: 0.20,
    electricity_export_price: 0.05,
    annual_energy_import_kwh: 100000,
    annual_energy_export_kwh: 0,
    annual_peak_demand_kw: 100,
    demand_charge_per_kw_month: 15
  },
  usage: {
    self_consumption_ratio: 0.70,
    battery_cycles_per_year: 365,
    degradation_rate_year1: 0.02,
    degradation_rate_after: 0.005
  },
  timeline: {
    project_lifespan_years: 20,
    discount_rate: 0.08,
    inflation_rate: 0.02
  }
};

function InputField({ label, value, onChange, min, max, step, unit }: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
}) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
          min={min}
          max={max}
          step={step || 1}
          className="form-input"
          style={{ flex: 1 }}
        />
        {unit && <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{unit}</span>}
      </div>
    </div>
  );
}

function ResultCard({ label, value, unit, highlight }: {
  label: string;
  value: number;
  unit?: string;
  highlight?: boolean;
}) {
  return (
    <div
      className="stat-card"
      style={{
        background: highlight ? "var(--success-bg)" : "var(--card-bg)",
        border: highlight ? "2px solid var(--success)" : "1px solid var(--border)",
        textAlign: "center",
        overflow: "hidden"
      }}
    >
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: highlight ? "var(--success)" : "var(--text)", fontSize: 18, wordBreak: "break-word", lineHeight: 1.2 }}>
        {typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : value}
        {unit && <span style={{ fontSize: 12, marginLeft: 4 }}>{unit}</span>}
      </div>
    </div>
  );
}

export function ROIPage() {
  const { siteId } = useParams();
  const qc = useQueryClient();
  const [input, setInput] = useState<ROIInput>(defaultInput);
  const [result, setResult] = useState<ROIResult | null>(null);
  const [activeTab, setActiveTab] = useState<"calculator" | "scenarios">("calculator");

  const scenariosQuery = useQuery({
    queryKey: ["roi", "scenarios", siteId],
    queryFn: () => listROIScenarios(siteId!),
    enabled: !!siteId
  });

  const calculateMutation = useMutation({
    mutationFn: () => calculateROI(siteId!, input),
    onSuccess: (data) => setResult(data)
  });

  const saveMutation = useMutation({
    mutationFn: () => createROIScenario(siteId!, input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roi", "scenarios", siteId] })
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteROIScenario(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roi", "scenarios", siteId] })
  });

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const updateSystem = (field: keyof ROIInput["system"], value: number) =>
    setInput((prev) => ({ ...prev, system: { ...prev.system, [field]: value } }));

  const updateFinancial = (field: keyof ROIInput["financial"], value: number) =>
    setInput((prev) => ({ ...prev, financial: { ...prev.financial, [field]: value } }));

  const updateUsage = (field: keyof ROIInput["usage"], value: number) =>
    setInput((prev) => ({ ...prev, usage: { ...prev.usage, [field]: value } }));

  const updateTimeline = (field: keyof ROIInput["timeline"], value: number) =>
    setInput((prev) => ({ ...prev, timeline: { ...prev.timeline, [field]: value } }));

  return (
    <div className="page-content">
      <PageHeader title="ROI Calculator" subtitle={siteId} />

      <div className="tabs">
        <button
          onClick={() => setActiveTab("calculator")}
          className={`tab ${activeTab === "calculator" ? "active" : ""}`}
        >
          Calculator
        </button>
        <button
          onClick={() => setActiveTab("scenarios")}
          className={`tab ${activeTab === "scenarios" ? "active" : ""}`}
        >
          Saved Scenarios
        </button>
      </div>

      {activeTab === "calculator" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <Card title="System Configuration">
            <InputField label="Battery Capacity" value={input.system.battery_capacity_kwh} onChange={(v) => updateSystem("battery_capacity_kwh", v)} unit="kWh" />
            <InputField label="Battery Power" value={input.system.battery_power_kw} onChange={(v) => updateSystem("battery_power_kw", v)} unit="kW" />
            <InputField label="Solar Capacity" value={input.system.solar_capacity_kwp} onChange={(v) => updateSystem("solar_capacity_kwp", v)} unit="kWp" />
            <InputField label="Round-trip Efficiency" value={input.system.round_trip_efficiency * 100} onChange={(v) => updateSystem("round_trip_efficiency", v / 100)} min={50} max={100} unit="%" />
          </Card>

          <Card title="Financial Parameters">
            <InputField label="Installation Cost" value={input.financial.installation_cost} onChange={(v) => updateFinancial("installation_cost", v)} unit="USD" />
            <InputField label="Annual Maintenance Cost" value={input.financial.annual_maintenance_cost} onChange={(v) => updateFinancial("annual_maintenance_cost", v)} unit="USD" />
            <InputField label="Import Price" value={input.financial.electricity_import_price} onChange={(v) => updateFinancial("electricity_import_price", v)} step={0.01} unit="USD/kWh" />
            <InputField label="Export Price" value={input.financial.electricity_export_price} onChange={(v) => updateFinancial("electricity_export_price", v)} step={0.01} unit="USD/kWh" />
            <InputField label="Annual Energy Import" value={input.financial.annual_energy_import_kwh} onChange={(v) => updateFinancial("annual_energy_import_kwh", v)} unit="kWh" />
            <InputField label="Peak Demand" value={input.financial.annual_peak_demand_kw} onChange={(v) => updateFinancial("annual_peak_demand_kw", v)} unit="kW" />
            <InputField label="Demand Charge" value={input.financial.demand_charge_per_kw_month} onChange={(v) => updateFinancial("demand_charge_per_kw_month", v)} unit="USD/kW/mo" />
          </Card>

          <Card title="Usage & Degradation">
            <InputField label="Self-Consumption Ratio" value={input.usage.self_consumption_ratio * 100} onChange={(v) => updateUsage("self_consumption_ratio", v / 100)} min={0} max={100} unit="%" />
            <InputField label="Battery Cycles/Year" value={input.usage.battery_cycles_per_year} onChange={(v) => updateUsage("battery_cycles_per_year", v)} />
            <InputField label="Degradation Year 1" value={input.usage.degradation_rate_year1 * 100} onChange={(v) => updateUsage("degradation_rate_year1", v / 100)} min={0} max={100} unit="%" />
            <InputField label="Degradation After Year 1" value={input.usage.degradation_rate_after * 100} onChange={(v) => updateUsage("degradation_rate_after", v / 100)} min={0} max={100} unit="%/yr" />
          </Card>

          <Card title="Project Timeline">
            <InputField label="Project Lifespan" value={input.timeline.project_lifespan_years} onChange={(v) => updateTimeline("project_lifespan_years", v)} min={1} max={50} unit="years" />
            <InputField label="Discount Rate" value={input.timeline.discount_rate * 100} onChange={(v) => updateTimeline("discount_rate", v / 100)} min={0} max={100} unit="%" />
            <InputField label="Inflation Rate" value={input.timeline.inflation_rate * 100} onChange={(v) => updateTimeline("inflation_rate", v / 100)} min={0} max={100} unit="%" />
          </Card>

          <div style={{ gridColumn: "1 / -1", display: "flex", gap: 12 }}>
            <button
              onClick={() => calculateMutation.mutate()}
              disabled={calculateMutation.isPending}
              className="btn btn-primary"
            >
              {calculateMutation.isPending ? <LoadingSpinner /> : "Calculate ROI"}
            </button>
            <button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || !result}
              className="btn btn-secondary"
            >
              Save Scenario
            </button>
          </div>
        </div>
      )}

      {activeTab === "scenarios" && (
        <Card title="Saved Scenarios">
          {scenariosQuery.isLoading ? (
            <LoadingSpinner />
          ) : scenariosQuery.isError ? (
            <ErrorBanner error={scenariosQuery.error as Error} />
          ) : scenariosQuery.data?.items.length === 0 ? (
            <div className="deferred-box">No saved scenarios yet. Use the calculator to create one.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {scenariosQuery.data?.items.map((scenario) => (
                <div
                  key={scenario.id}
                  className="card"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr auto",
                    gap: 16,
                    alignItems: "center"
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600 }}>{scenario.name}</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {scenario.battery_capacity_kwh}kWh / {scenario.solar_capacity_kwp}kWp
                    </div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Annual Savings</div>
                    <div style={{ fontWeight: 600, color: "var(--success)" }}>${scenario.annual_savings?.toLocaleString()}</div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Payback</div>
                    <div style={{ fontWeight: 600 }}>{scenario.payback_years} yrs</div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>ROI</div>
                    <div style={{ fontWeight: 600 }}>{scenario.roi_percentage}%</div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>NPV</div>
                    <div style={{ fontWeight: 600, color: scenario.npv && scenario.npv > 0 ? "var(--success)" : "var(--error)" }}>
                      ${scenario.npv?.toLocaleString()}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm("Delete this scenario?")) {
                        deleteMutation.mutate(scenario.id);
                      }
                    }}
                    className="btn btn-danger btn-sm"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {result && (
        <div style={{ marginTop: 24 }}>
          <Card title="ROI Analysis Results">
            <div className="stats-grid" style={{ marginBottom: 24 }}>
              <ResultCard label="Annual Savings" value={result.annual_savings} unit="USD/yr" highlight />
              <ResultCard label="Simple Payback" value={result.payback_years} unit="years" />
              <ResultCard label="Total ROI" value={result.roi_percentage} unit="%" highlight={result.roi_percentage > 100} />
              <ResultCard label="NPV" value={result.npv} unit="USD" highlight={result.npv > 0} />
              <ResultCard label="IRR" value={result.irr_percentage} unit="%" />
            </div>

            <h4 style={{ marginBottom: 12 }}>Year-by-Year Projection</h4>
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Year</th>
                    <th style={{ textAlign: "right" }}>Annual Savings</th>
                    <th style={{ textAlign: "right" }}>Cumulative</th>
                    <th style={{ textAlign: "right" }}>NPV</th>
                    <th style={{ textAlign: "center" }}>Break-even</th>
                  </tr>
                </thead>
                <tbody>
                  {result.year_by_year.map((year) => (
                    <tr key={year.year} style={{ background: year.break_even ? "var(--success-bg)" : "transparent" }}>
                      <td>Year {year.year}</td>
                      <td style={{ textAlign: "right" }}>
                        ${year.annual_savings.toLocaleString()}
                      </td>
                      <td style={{ textAlign: "right", fontWeight: year.break_even ? 600 : 400 }}>
                        ${year.cumulative_savings.toLocaleString()}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        ${year.npv.toLocaleString()}
                      </td>
                      <td style={{ textAlign: "center" }}>
                        {year.break_even ? "✓" : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
