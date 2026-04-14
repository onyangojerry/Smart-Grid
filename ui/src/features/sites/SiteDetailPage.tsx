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

  // Map latest_state to StatCard format
  const stats = [
    { label: "PV", value: latest_state.pv_kw, unit: "kW" },
    { label: "Load", value: latest_state.load_kw, unit: "kW" },
    { label: "Battery SOC", value: latest_state.battery_soc, unit: "%" },
    { label: "Battery Power", value: latest_state.battery_power_kw, unit: "kW" },
    { label: "Grid Import", value: latest_state.grid_import_kw, unit: "kW" },
    { label: "Grid Export", value: latest_state.grid_export_kw, unit: "kW" },
    { label: "Import Price", value: latest_state.price_import, unit: "$/kWh" },
  ];

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <PageHeader title={site.name || "Site Dashboard"} subtitle={siteId} />

      <Card title="Live telemetry">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(170px,1fr))", gap: 8 }}>
          {stats.map((stat) => (
            <StatCard
              key={stat.label}
              label={stat.label}
              value={stat.value}
              unit={stat.unit}
              ts={latest_state.ts}
              quality={latest_state.online ? "good" : "bad"}
              stale={isStale(latest_state.ts, 60)}
            />
          ))}
        </div>
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12 }}>
        <Card title="Latest optimization">
          {latestRun ? (
            <div style={{ display: "grid", gap: 8 }}>
              <div>Mode: {latestRun.mode}</div>
              <ExplanationPanel
                explanation={latestRun.explanation || latestRun.selected_action?.explanation || null}
              />
            </div>
          ) : (
            <div>No optimization runs yet.</div>
          )}
        </Card>
        <Card title="Savings summary">
          {savings ? (
            <div style={{ display: "grid", gap: 6 }}>
              <div>Baseline: {savings.baseline_cost.toFixed(2)}</div>
              <div>Optimized: {savings.optimized_cost.toFixed(2)}</div>
              <div>Saving: {savings.savings_percent.toFixed(1)}%</div>
            </div>
          ) : (
            <div>No savings summary available.</div>
          )}
        </Card>
      </div>

    </div>
  );
}
