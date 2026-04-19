import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { getSiteDashboard } from "../../api/sites";
import { queryKeys } from "../../api/queryKeys";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { usePollInterval } from "../../hooks/usePollInterval";
import { ExplanationPanel } from "../optimization/ExplanationPanel";
import { PiggyBank, Zap, Activity, ShieldCheck, Leaf } from "lucide-react";
import "../../styles/features.css";

export function SiteDetailPage() {
  const { siteId } = useParams();
  
  const { scrollYProgress } = useScroll();
  const opacities = [
    useTransform(scrollYProgress, [0, 0.25], [1, 0]),
    useTransform(scrollYProgress, [0.25, 0.5, 0.75], [0, 1, 0]),
    useTransform(scrollYProgress, [0.75, 1], [0, 1]),
  ];

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const dashboardQuery = useQuery({
    queryKey: queryKeys.siteDashboard(siteId),
    queryFn: () => getSiteDashboard(siteId),
    refetchInterval: usePollInterval("telemetry")
  });

  const { data, isLoading, isError, error } = dashboardQuery;

  if (isLoading) return <LoadingSpinner />;
  if (isError) return <ErrorBanner error={error as Error} />;
  if (!data) return null;

  const { latest_state, optimization_runs, savings, site } = data;
  const latestRun = optimization_runs?.[0];

  const images = [
    "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?auto=format&fit=crop&q=80&w=2000", // High-tech control room
    "https://images.unsplash.com/photo-1466611653911-95282fc3656b?auto=format&fit=crop&q=80&w=2000", // Wind/Solar field
    "https://images.unsplash.com/photo-1542601906990-b4d3fb773b09?auto=format&fit=crop&q=80&w=2000", // Nature/Sustainability
  ];

  return (
    <div className="scrolly-container">
      <div className="scrolly-stage">
        {images.map((src, i) => (
          <motion.img key={src} src={src} className="stage-image" style={{ opacity: opacities[i] }} />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Deep dive into {site.name || "Overview"}</div>
      </div>

      <div className="scrolly-story">
        
        {/* Site Hero */}
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">{site.name || "Site Overview"}</h1>
            <p className="story-subtitle">System intelligence is active and optimizing your energy flow.</p>
            <div style={{ display: "flex", gap: "2rem", justifyContent: "center", marginTop: "3rem" }}>
               <div style={{ textAlign: "center" }}>
                 <span className="hero-label">Status</span>
                 <div style={{ color: "#4ade80", fontWeight: 800, fontSize: "1.5rem" }}>OPTIMIZING</div>
               </div>
               <div style={{ textAlign: "center" }}>
                 <span className="hero-label">Connectivity</span>
                 <div style={{ color: "#4ade80", fontWeight: 800, fontSize: "1.5rem" }}>ONLINE</div>
               </div>
            </div>
          </motion.div>
        </section>

        {/* Impact Story */}
        <section className="story-section">
          <div className="story-content-narrative">
            <h2 className="story-title" style={{ fontSize: "3rem" }}>Realized Impact</h2>
            <div style={{ display: "grid", gap: "3rem", marginTop: "2rem" }}>
              <div style={{ borderLeft: "6px solid var(--primary)", paddingLeft: "2rem" }}>
                <span className="hero-label"><PiggyBank size={20} /> Financial Gain</span>
                <span className="hero-metric">${savings ? (savings.baseline_cost - savings.optimized_cost).toFixed(2) : "0.00"}</span>
                <p className="story-body">
                  {savings ? `${savings.savings_percent.toFixed(1)}% optimization gain` : "Calculating impact..."}
                  <br/>Smart decisions are compounding into real capital.
                </p>
              </div>
              <div style={{ borderLeft: "6px solid #4ade80", paddingLeft: "2rem" }}>
                <span className="hero-label"><Leaf size={20} /> Environmental Legacy</span>
                <span className="hero-metric">0.4 Trees</span>
                <p className="story-body">
                  You've avoided significant CO2 emissions this month by shifting your demand to cleaner hours.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Logic & Vitals */}
        <section className="story-section right">
          <div className="story-content-narrative">
            <h2 className="story-title" style={{ fontSize: "2.5rem" }}>The Decision Mind</h2>
            {latestRun ? (
              <div style={{ background: "rgba(255,255,255,0.1)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: "1.5rem", color: "#4ade80" }}>
                  <ShieldCheck size={24} />
                  <span style={{ fontWeight: 800 }}>Autonomous Logic Active</span>
                </div>
                <ExplanationPanel
                  explanation={latestRun.explanation || latestRun.selected_action?.explanation || null}
                />
              </div>
            ) : (
              <p className="story-body">Waiting for the first decision... Your system is observing and preparing.</p>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginTop: "3rem" }}>
               <StatItem label="Battery SoC" value={latest_state.battery_soc} unit="%" />
               <StatItem label="Grid Power" value={Math.abs(latest_state.grid_import_kw - latest_state.grid_export_kw)} unit="kW" />
               <StatItem label="PV Generation" value={latest_state.pv_kw} unit="kW" />
               <StatItem label="House Load" value={latest_state.load_kw} unit="kW" />
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}

function StatItem({ label, value, unit }: { label: string, value: number, unit: string }) {
  return (
    <div style={{ padding: "1.5rem", borderRadius: "1rem", background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.1)" }}>
      <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "rgba(255,255,255,0.6)", textTransform: "uppercase", marginBottom: "0.5rem" }}>{label}</div>
      <div style={{ fontSize: "2rem", fontWeight: 800, color: "white" }}>{value.toFixed(1)}<span style={{ fontSize: "1rem", marginLeft: "0.25rem", opacity: 0.5 }}>{unit}</span></div>
    </div>
  );
}
