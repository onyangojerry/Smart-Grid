import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { runSimulation } from "../../api/simulation";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { SimulationForm } from "../../components/forms/SimulationForm";
import { StatCard } from "../../components/ui/StatCard";
import { DataTable } from "../../components/tables/DataTable";
import { ActionHistoryChart } from "../../components/charts/ActionHistoryChart";
import type { SimulationRunDetail } from "../../types";
import "../../styles/features.css";

export function SimulationPage() {
  const { siteId } = useParams();
  const [latestResult, setLatestResult] = useState<SimulationRunDetail | null>(null);
  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const mutation = useMutation({
    mutationFn: ({ siteId, body }: { siteId: string; body: import("../../types").SimulationRunBody }) =>
      runSimulation(siteId, body),
    onSuccess: (result) => setLatestResult(result)
  });

  return (
    <div className="page-content">
      <PageHeader title="Simulation" subtitle={siteId} />
      <Card title="Run simulation">
        <SimulationForm onSubmit={(body) => mutation.mutate({ siteId, body })} loading={mutation.isPending} />
        {mutation.isError ? <ErrorBanner error={mutation.error as Error} /> : null}
      </Card>
      
      {latestResult ? (
        <>
          <div className="stats-grid">
            <StatCard label="Baseline cost" value={latestResult.baseline_cost} unit="USD" />
            <StatCard label="Optimized cost" value={latestResult.optimized_cost} unit="USD" />
            <StatCard label="Savings %" value={latestResult.savings_percent} unit="%" />
            <StatCard label="Battery cycles" value={latestResult.battery_cycles} unit="" />
            <StatCard label="Self-consumption %" value={latestResult.self_consumption_percent} unit="%" />
            <StatCard label="Peak demand reduction" value={latestResult.peak_demand_reduction} unit="kW" />
          </div>
          <Card title="Action history chart">
            <ActionHistoryChart
              points={latestResult.action_history.map((a, idx) => ({
                ts: String(idx),
                action: a.action,
                target_power_kw: a.target_power_kw,
                score: 0
              }))}
            />
          </Card>
          <Card title="Action history table">
            <DataTable
              rows={latestResult.action_history}
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

      <Card title="Status">
        <div className="deferred-box">DEFERRED: async simulation detail endpoint `/api/v1/sites/{site_id}/simulation/{'{sim_id}'}` is not implemented.</div>
      </Card>
    </div>
  );
}
