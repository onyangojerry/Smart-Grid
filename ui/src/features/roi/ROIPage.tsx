import React, { useState, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { calculateROI, createROIScenario, deleteROIScenario, listROIScenarios } from "../../api/roi";
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

function InputField({ label, value, onChange, min, max, step, unit }: any) {
  return (
    <div className="form-group" style={{ marginBottom: "1.5rem" }}>
      <label className="form-label" style={{ color: "rgba(255,255,255,0.7)" }}>{label}</label>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
          min={min}
          max={max}
          step={step || 1}
          className="form-input"
          style={{ flex: 1, background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.2)", color: "white" }}
        />
        {unit && <span style={{ fontSize: 14, color: "var(--primary)", fontWeight: 700, minWidth: "50px" }}>{unit}</span>}
      </div>
    </div>
  );
}

export function ROIPage() {
  const { siteId } = useParams();
  const qc = useQueryClient();
  const [input, setInput] = useState<ROIInput>(defaultInput);
  const [result, setResult] = useState<ROIResult | null>(null);

  const { scrollYProgress } = useScroll();
  const opacities = [
    useTransform(scrollYProgress, [0, 0.2], [1, 0]),           // Intro
    useTransform(scrollYProgress, [0.2, 0.4, 0.6], [0, 1, 0]), // Inputs
    useTransform(scrollYProgress, [0.6, 0.8], [0, 1]),         // Results
  ];

  const calculateMutation = useMutation({
    mutationFn: () => calculateROI(siteId!, input),
    onSuccess: (data) => setResult(data)
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

  const images = [
    "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&q=80&w=2000", // ROI/Charts
    "https://images.unsplash.com/photo-1554224155-169641357599?auto=format&fit=crop&q=80&w=2000", // Calculator/Finance
    "https://images.unsplash.com/photo-1518186239751-2477cf41d49e?auto=format&fit=crop&q=80&w=2000", // Green/Growth
  ];

  return (
    <div className="scrolly-container">
      <div className="scrolly-stage">
        {images.map((src, i) => (
          <motion.img key={src} src={src} className="stage-image" style={{ opacity: opacities[i] }} />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Calculate your ROI Story</div>
      </div>

      <div className="scrolly-story">
        
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">ROI Stories</h1>
            <p className="story-subtitle">The financial logic of sustainable energy for {siteId}</p>
            <p className="story-body">
              Every system is an investment in the future. By balancing upfront costs against decade-long savings, we help you visualize the moment your intelligence pays for itself.
            </p>
          </motion.div>
        </section>

        <section className="story-section" style={{ minHeight: "150vh" }}>
          <div className="story-content-narrative" style={{ maxWidth: "1000px" }}>
            <h2 className="story-title" style={{ fontSize: "3rem" }}>Configure Your Scenario</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "3rem", marginTop: "3rem" }}>
              
              <div style={{ background: "rgba(0,0,0,0.4)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
                <h3 style={{ marginBottom: "1.5rem", color: "var(--primary)" }}>System & Usage</h3>
                <InputField label="Battery Capacity" value={input.system.battery_capacity_kwh} onChange={(v: any) => updateSystem("battery_capacity_kwh", v)} unit="kWh" />
                <InputField label="Solar Capacity" value={input.system.solar_capacity_kwp} onChange={(v: any) => updateSystem("solar_capacity_kwp", v)} unit="kWp" />
                <InputField label="Self-Consumption" value={input.usage.self_consumption_ratio * 100} onChange={(v: any) => updateUsage("self_consumption_ratio", v / 100)} unit="%" />
                <InputField label="Battery Cycles/Year" value={input.usage.battery_cycles_per_year} onChange={(v: any) => updateUsage("battery_cycles_per_year", v)} />
              </div>

              <div style={{ background: "rgba(0,0,0,0.4)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
                <h3 style={{ marginBottom: "1.5rem", color: "var(--primary)" }}>Financials</h3>
                <InputField label="Installation Cost" value={input.financial.installation_cost} onChange={(v: any) => updateFinancial("installation_cost", v)} unit="USD" />
                <InputField label="Import Price" value={input.financial.electricity_import_price} onChange={(v: any) => updateFinancial("electricity_import_price", v)} step={0.01} unit="$/kWh" />
                <InputField label="Peak Demand" value={input.financial.annual_peak_demand_kw} onChange={(v: any) => updateFinancial("annual_peak_demand_kw", v)} unit="kW" />
                <InputField label="Demand Charge" value={input.financial.demand_charge_per_kw_month} onChange={(v: any) => updateFinancial("demand_charge_per_kw_month", v)} unit="$/kW/mo" />
              </div>

            </div>
            
            <div style={{ textAlign: "center", marginTop: "4rem" }}>
              <button 
                onClick={() => calculateMutation.mutate()} 
                disabled={calculateMutation.isPending}
                className="btn btn-lg btn-primary"
              >
                {calculateMutation.isPending ? "Calculating Logic..." : "Generate ROI Analysis"}
              </button>
            </div>
          </div>
        </section>

        {result && (
          <section className="story-section">
            <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
              <h2 className="story-title" style={{ fontSize: "3rem" }}>The Verdict</h2>
              
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "2rem", marginTop: "3rem" }}>
                <motion.div initial={{ scale: 0.9 }} whileInView={{ scale: 1 }} style={{ background: "rgba(0,0,0,0.5)", padding: "2rem", borderRadius: "1rem", borderTop: "6px solid #4ade80" }}>
                  <span className="hero-label">Annual Savings</span>
                  <span className="hero-metric" style={{ fontSize: "3rem", color: "#4ade80" }}>${result.annual_savings.toLocaleString()}</span>
                </motion.div>
                <motion.div initial={{ scale: 0.9 }} whileInView={{ scale: 1 }} style={{ background: "rgba(0,0,0,0.5)", padding: "2rem", borderRadius: "1rem", borderTop: "6px solid var(--primary)" }}>
                  <span className="hero-label">Simple Payback</span>
                  <span className="hero-metric" style={{ fontSize: "3rem" }}>{result.payback_years} <span style={{ fontSize: "1.5rem" }}>yrs</span></span>
                </motion.div>
                <motion.div initial={{ scale: 0.9 }} whileInView={{ scale: 1 }} style={{ background: "rgba(0,0,0,0.5)", padding: "2rem", borderRadius: "1rem", borderTop: "6px solid #60a5fa" }}>
                  <span className="hero-label">Project NPV</span>
                  <span className="hero-metric" style={{ fontSize: "3rem", color: "#60a5fa" }}>${result.npv.toLocaleString()}</span>
                </motion.div>
              </div>

              <div style={{ marginTop: "4rem", background: "rgba(0,0,0,0.4)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
                <h4 style={{ marginBottom: "2rem", fontSize: "1.5rem" }}>Projected Growth</h4>
                <div className="data-table-container" style={{ background: "transparent", border: "none" }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th style={{ color: "var(--primary)" }}>Year</th>
                        <th style={{ textAlign: "right" }}>Annual Savings</th>
                        <th style={{ textAlign: "right" }}>Cumulative</th>
                        <th style={{ textAlign: "center" }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.year_by_year.filter(y => y.year % 5 === 0 || y.break_even || y.year === 1).map((year) => (
                        <tr key={year.year} style={{ borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
                          <td style={{ color: "white" }}>Year {year.year}</td>
                          <td style={{ textAlign: "right", color: "white" }}>${year.annual_savings.toLocaleString()}</td>
                          <td style={{ textAlign: "right", color: year.break_even ? "#4ade80" : "white", fontWeight: year.break_even ? 800 : 400 }}>
                            ${year.cumulative_savings.toLocaleString()}
                          </td>
                          <td style={{ textAlign: "center" }}>
                            {year.break_even ? <span style={{ background: "#4ade80", color: "#000", padding: "4px 8px", borderRadius: "4px", fontSize: "10px", fontWeight: 900 }}>BREAK EVEN</span> : ""}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>
        )}

      </div>
    </div>
  );
}
