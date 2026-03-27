import React, { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useParams, useSearchParams } from "react-router-dom";
import { runSimulation, getSimulationDetail } from "../../api/simulation";
import { queryKeys } from "../../api/queryKeys";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { SimulationForm } from "../../components/forms/SimulationForm";
import { StatCard } from "../../components/ui/StatCard";
import { DataTable } from "../../components/tables/DataTable";
import { ActionHistoryChart } from "../../components/charts/ActionHistoryChart";
import type { SimulationRunDetail } from "../../types";
import "../../styles/features.css";

export function SimulationPage() {
  const { siteId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const simId = searchParams.get("simId");
  const [latestResult, setLatestResult] = useState<SimulationRunDetail | null>(null);

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const detailQuery = useQuery({
    queryKey: queryKeys.simulation(siteId, simId!),
    queryFn: () => getSimulationDetail(siteId, simId!),
    enabled: !!simId
  });

  const mutation = useMutation({
    mutationFn: ({ siteId, body }: { siteId: string; body: import("../../types").SimulationRunBody }) =>
      runSimulation(siteId, body),
    onSuccess: (result) => {
      setLatestResult(result);
      if (result.id) {
        setSearchParams({ simId: result.id });
      }
    }
  });

  const displayResult = latestResult || detailQuery.data;

  return (
    <div className="page-content">
      <PageHeader title="Simulation" subtitle={siteId} />
      <Card title="Run simulation">
        <SimulationForm onSubmit={(body) => mutation.mutate({ siteId, body })} loading={mutation.isPending} />
        {mutation.isError ? <ErrorBanner error={mutation.error as Error} message="Failed to run simulation. Please check input values." /> : null}
      </Card>
      
      {detailQuery.isLoading ? <LoadingSpinner /> : null}
      {detailQuery.isError ? <ErrorBanner error={detailQuery.error as Error} message="Failed to load simulation details." /> : null}

      {displayResult ? (
        <>
          <div className="stats-grid">
            <StatCard label="Baseline cost" value={displayResult.baseline_cost} unit="USD" />
            <StatCard label="Optimized cost" value={displayResult.optimized_cost} unit="USD" />
            <StatCard label="Savings %" value={displayResult.savings_percent} unit="%" />
            <StatCard label="Battery cycles" value={displayResult.battery_cycles} unit="" />
            <StatCard label="Self-consumption %" value={displayResult.self_consumption_percent} unit="%" />
            <StatCard label="Peak demand reduction" value={displayResult.peak_demand_reduction} unit="kW" />
          </div>
          <Card title="Action history chart">
            <ActionHistoryChart
              points={displayResult.action_history.map((a, idx) => ({
                ts: String(idx),
                action: a.action,
                target_power_kw: a.target_power_kw,
                score: 0
              }))}
            />
          </Card>
          <Card title="Action history table">
            <DataTable
              rows={displayResult.action_history}
              getRowKey={(r) => `${r.step}-${r.action}-${r.target_power_kw}`}
              columns={[
                { key: "step", header: "step", render: (r) => r.step },
                { key: "action", header: "action", render: (r) => r.action },
                { key: "target", header: "target_power_kw", render: (r) => r.target_power_kw.toFixed(2) },
                { key: "soc", header: "soc", render: (r) => r.soc.toFixed(2) }
              ]}
            />
          </Card>
        </>
      ) : null}
    </div>
  );
}
