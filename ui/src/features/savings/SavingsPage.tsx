import React, { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getSavingsSummary } from "../../api/savings";
import { queryKeys } from "../../api/queryKeys";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { StatCard } from "../../components/ui/StatCard";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import "../../styles/features.css";

export function SavingsPage() {
  const { siteId } = useParams();
  const to = useMemo(() => new Date().toISOString(), []);
  const from = useMemo(() => new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(), []);
  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const query = useQuery({ queryKey: queryKeys.savings(siteId), queryFn: () => getSavingsSummary(siteId, from, to) });

  if (query.isLoading) return <LoadingSpinner />;
  if (query.isError) return <ErrorBanner error={query.error as Error} onRetry={() => query.refetch()} />;
  if (!query.data) return <ErrorBanner error={new Error("No savings data returned")} onRetry={() => query.refetch()} />;

  const data = query.data;
  return (
    <div className="page-content">
      <PageHeader title="Savings" subtitle={siteId} />
      <div className="stats-grid">
        <StatCard label="Baseline cost" value={data.baseline_cost} unit="USD" />
        <StatCard label="Optimized cost" value={data.optimized_cost} unit="USD" />
        <StatCard label="Savings amount" value={data.baseline_cost - data.optimized_cost} unit="USD" />
        <StatCard label="Savings %" value={data.savings_percent} unit="%" />
      </div>
      <Card title="Methodology">
        <div style={{ color: "var(--text-muted)", fontSize: 14 }}>Computed from command effects and import price over requested window.</div>
      </Card>
    </div>
  );
}
