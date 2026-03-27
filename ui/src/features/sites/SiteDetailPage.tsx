import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getOptimizationRuns } from "../../api/optimization";
import { getSavingsSummary } from "../../api/savings";
import { getTelemetryLatest } from "../../api/telemetry";
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

  const telemetryQuery = useQuery({
    queryKey: queryKeys.telemetryLatest(siteId),
    queryFn: () => getTelemetryLatest(siteId),
    refetchInterval: usePollInterval("telemetry")
  });
  const optimizationQuery = useQuery({
    queryKey: queryKeys.optimizationRuns(siteId),
    queryFn: () => getOptimizationRuns(siteId),
    refetchInterval: usePollInterval("optimization")
  });
  const savingsQuery = useQuery({
    queryKey: queryKeys.savings(siteId),
    queryFn: () => getSavingsSummary(siteId)
  });

  const latestRun = optimizationQuery.data?.[0];

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <PageHeader title="Site Dashboard" subtitle={siteId} />

      <Card title="Live telemetry">
        {telemetryQuery.isLoading ? (
          <LoadingSpinner />
        ) : telemetryQuery.isError ? (
          <ErrorBanner error={telemetryQuery.error as Error} />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(170px,1fr))", gap: 8 }}>
            {Object.entries(telemetryQuery.data || {}).map(([key, value]) => (
              <StatCard
                key={key}
                label={key}
                value={value.value}
                unit={value.unit}
                ts={value.ts}
                quality={value.quality}
                stale={isStale(value.ts, 60)}
              />
            ))}
          </div>
        )}
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12 }}>
        <Card title="Latest optimization">
          {optimizationQuery.isLoading ? (
            <LoadingSpinner />
          ) : optimizationQuery.isError ? (
            <ErrorBanner error={optimizationQuery.error as Error} />
          ) : latestRun ? (
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
          {savingsQuery.isLoading ? (
            <LoadingSpinner />
          ) : savingsQuery.isError ? (
            <ErrorBanner error={savingsQuery.error as Error} />
          ) : savingsQuery.data ? (
            <div style={{ display: "grid", gap: 6 }}>
              <div>Baseline: {savingsQuery.data.baseline_cost.toFixed(2)}</div>
              <div>Optimized: {savingsQuery.data.optimized_cost.toFixed(2)}</div>
              <div>Saving: {savingsQuery.data.savings_percent.toFixed(1)}%</div>
            </div>
          ) : (
            <div>No savings summary available.</div>
          )}
        </Card>
      </div>

    </div>
  );
}
