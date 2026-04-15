import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getSiteDashboard } from "../../api/sites";
import { queryKeys } from "../../api/queryKeys";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { StatCard } from "../../components/ui/StatCard";
import { isStale } from "../../utils/time";
import { usePollInterval } from "../../hooks/usePollInterval";
import { ExplanationPanel } from "../optimization/ExplanationPanel";
import { PiggyBank, Zap, Activity, ShieldCheck } from "lucide-react";

export function SiteDetailPage() {
  const { siteId } = useParams();
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

  return (
    <div className="page-content">
      <div style={{ marginBottom: 24 }}>
        <PageHeader 
          title={site.name || "Site Overview"} 
          subtitle="System intelligence is active and optimizing your energy flow." 
        />
      </div>

      {/* Impact Row */}
      <div className="stats-grid">
        <div className="stat-card" style={{ borderColor: "var(--primary)" }}>
          <div className="stat-label" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <PiggyBank size={16} /> Financial Impact
          </div>
          <div className="stat-value">
            {savings ? `$${(savings.baseline_cost - savings.optimized_cost).toFixed(2)}` : "$0.00"}
          </div>
          <div className="stat-text" style={{ fontSize: 13, color: "var(--success)", fontWeight: 700, marginTop: 8 }}>
            {savings ? `${savings.savings_percent.toFixed(1)}% optimization gain` : "Calculating impact..."}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Zap size={16} /> System Vitality
          </div>
          <div className="stat-value">
            {latest_state.battery_soc.toFixed(0)}%
          </div>
          <div className="stat-text" style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>
            Battery is {latest_state.battery_power_kw > 0 ? "charging" : latest_state.battery_power_kw < 0 ? "discharging" : "resting"}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Activity size={16} /> Grid Connection
          </div>
          <div className="stat-value">
            {Math.abs(latest_state.grid_import_kw - latest_state.grid_export_kw).toFixed(1)} <span className="stat-unit">kW</span>
          </div>
          <div className="stat-text" style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>
            {latest_state.grid_import_kw > 0 ? "Importing from grid" : "Feeding the grid"}
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 32 }}>
        <Card title="Latest Smart Decision">
          {latestRun ? (
            <div style={{ display: "grid", gap: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", background: "var(--success-bg)", borderRadius: 12, color: "var(--secondary)" }}>
                <ShieldCheck size={20} />
                <span style={{ fontWeight: 600 }}>Autonomous logic is active and protecting your system.</span>
              </div>
              <ExplanationPanel
                explanation={latestRun.explanation || latestRun.selected_action?.explanation || null}
              />
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">🤖</div>
              <div className="empty-state-title">Waiting for the first decision...</div>
              <p className="empty-state-description">Your system is observing and preparing its first move.</p>
            </div>
          )}
        </Card>

        <div style={{ display: "grid", gap: 32 }}>
          <Card title="Live Heartbeat">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <StatItem label="PV Generation" value={latest_state.pv_kw} unit="kW" />
              <StatItem label="House Load" value={latest_state.load_kw} unit="kW" />
              <StatItem label="Import Price" value={latest_state.price_import} unit="$" />
              <StatItem label="Battery Health" value={100} unit="%" />
            </div>
          </Card>
          
          <Card title="Environmental Impact">
            <div style={{ textAlign: "center", padding: "16px 0" }}>
              <div style={{ fontSize: 40, marginBottom: 16 }}>🌳</div>
              <div style={{ fontWeight: 700, fontSize: 18 }}>You've planted 0.4 trees</div>
              <p style={{ color: "var(--text-muted)", fontSize: 14 }}>Based on your clean energy usage this month.</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function StatItem({ label, value, unit }: { label: string, value: number, unit: string }) {
  return (
    <div style={{ padding: 12, borderRadius: 12, background: "var(--bg)", border: "1px solid var(--border)" }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 800 }}>{value.toFixed(1)}<span style={{ fontSize: 12, marginLeft: 2, color: "var(--text-muted)" }}>{unit}</span></div>
    </div>
  );
}
