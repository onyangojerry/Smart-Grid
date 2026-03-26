import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getOptimizationRuns, runOptimization, getOptimizationRunDetail } from "../../api/optimization";
import { queryKeys } from "../../api/queryKeys";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { OptimizationForm } from "../../components/forms/OptimizationForm";
import { ExplanationPanel } from "./ExplanationPanel";
import { DataTable } from "../../components/tables/DataTable";
import "../../styles/features.css";

export function OptimizationPage() {
  const { siteId } = useParams();
  const qc = useQueryClient();
  const [latestResultId, setLatestResultId] = useState<string | null>(null);
  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const runsQuery = useQuery({
    queryKey: queryKeys.optimizationRuns(siteId),
    queryFn: () => getOptimizationRuns(siteId),
    refetchInterval: 60_000
  });

  const optimizationRunDetailQuery = useQuery({
    queryKey: queryKeys.optimizationRunDetail(latestResultId!),
    queryFn: () => getOptimizationRunDetail(latestResultId!),
    enabled: !!latestResultId, // Only run if latestResultId is available
  });

  const runMutation = useMutation({
    mutationFn: ({ siteId, body }: { siteId: string; body: import("../../types").OptimizationRunBody }) =>
      runOptimization(siteId, body),
    onSuccess: (result) => {
      setLatestResultId(result.optimization_run_id || result.id || null);
      qc.invalidateQueries({ queryKey: queryKeys.optimizationRuns(siteId) });
      qc.invalidateQueries({ queryKey: queryKeys.telemetryLatest(siteId) });
      qc.invalidateQueries({ queryKey: queryKeys.commands(siteId) });
      // Invalidate the detail query as well, so it refetches with the new latestResultId
      qc.invalidateQueries({ queryKey: queryKeys.optimizationRunDetail(latestResultId!) });
    }
  });

  // Determine which explanation to show: from the latest mutation, or from the fetched detail query
  let currentExplanation = null;
  if (runMutation.data?.explanation) {
    currentExplanation = runMutation.data.explanation;
  } else if (optimizationRunDetailQuery.data?.explanation) {
    currentExplanation = optimizationRunDetailQuery.data.explanation;
  } else if (runMutation.data?.selected_action?.explanation) {
    currentExplanation = runMutation.data.selected_action.explanation;
  } else if (optimizationRunDetailQuery.data?.selected_action?.explanation) {
    currentExplanation = optimizationRunDetailQuery.data.selected_action.explanation;
  }

  return (
    <div className="page-content">
      <PageHeader title="Optimization" subtitle={siteId} />
      <Card title="Run optimization">
        <OptimizationForm onSubmit={(body) => runMutation.mutate({ siteId, body })} loading={runMutation.isPending} />
        {runMutation.isError ? <ErrorBanner error={runMutation.error as Error} /> : null}
        {currentExplanation ? (
          <div style={{ marginTop: 16 }}>
            <ExplanationPanel explanation={currentExplanation} />
          </div>
        ) : null}
      </Card>
      <Card title="Optimization runs history">
        {runsQuery.isLoading ? (
          <LoadingSpinner />
        ) : runsQuery.isError ? (
          <ErrorBanner error={runsQuery.error as Error} />
        ) : (
          <DataTable
            rows={runsQuery.data || []}
            getRowKey={(r) => r.id || r.optimization_run_id || Math.random().toString()}
            columns={[
              { key: "id", header: "Run", render: (r) => r.id || r.optimization_run_id || "—" },
              { key: "mode", header: "Mode", render: (r) => r.mode },
              { key: "decision", header: "Decision", render: (r) => r.explanation?.decision || r.selected_action?.command_type || "—" },
              { key: "summary", header: "Summary", render: (r) => r.explanation?.summary || r.selected_action?.explanation?.summary || "—" }
            ]}
          />
        )}
        {latestResultId ? <div style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>Latest run ID: {latestResultId}</div> : null}
        {optimizationRunDetailQuery.isFetching ? <LoadingSpinner /> : null}
        {optimizationRunDetailQuery.isError ? <ErrorBanner error={optimizationRunDetailQuery.error as Error} /> : null}
      </Card>
    </div>
  );
}
