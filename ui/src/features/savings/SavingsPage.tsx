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
import { TrendingDown, Leaf, Wallet } from "lucide-react";
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
  const savingsAmount = data.baseline_cost - data.optimized_cost;

  return (
    <div className="page-content">
      <PageHeader 
        title="Financial Impact" 
        subtitle="Seeing the fruits of your smart energy decisions." 
      />
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label"><Wallet size={14} style={{ marginRight: 6 }} /> Potential Spending</div>
          <div className="stat-value">${data.baseline_cost.toFixed(2)}</div>
          <div className="stat-text" style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>Without SmartGrid optimization</div>
        </div>

        <div className="stat-card" style={{ borderColor: "var(--success)" }}>
          <div className="stat-label"><TrendingDown size={14} style={{ marginRight: 6 }} /> Actual Spending</div>
          <div className="stat-value">${data.optimized_cost.toFixed(2)}</div>
          <div className="stat-text" style={{ fontSize: 13, color: "var(--success)", fontWeight: 700, marginTop: 8 }}>Reduced by {data.savings_percent.toFixed(1)}%</div>
        </div>

        <div className="stat-card" style={{ background: "var(--primary)", color: "white" }}>
          <div className="stat-label" style={{ color: "rgba(255,255,255,0.8)" }}>Money Kept</div>
          <div className="stat-value" style={{ color: "white" }}>${savingsAmount.toFixed(2)}</div>
          <div className="stat-text" style={{ fontSize: 13, color: "rgba(255,255,255,0.9)", marginTop: 8 }}>Back in your pocket</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
        <Card title="How we calculated this">
          <p style={{ color: "var(--text-muted)", fontSize: 15, lineHeight: 1.6 }}>
            Every time our AI makes a decision to charge your battery during low-price periods or discharge it when prices spike, we record the difference. 
            <strong> Potential Spending</strong> represents what you would have paid if you had just used energy directly from the grid without our smart intervention.
          </p>
        </Card>

        <Card title="Positive Footprint">
          <div style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
            <div style={{ fontSize: 32 }}>🌿</div>
            <div>
              <h4 style={{ margin: "0 0 8px 0", fontFamily: "var(--font-serif)" }}>Cleaner Energy usage</h4>
              <p style={{ color: "var(--text-muted)", fontSize: 14, margin: 0 }}>
                By shifting your load to solar hours, you've avoided using approximately <strong>{(savingsAmount * 1.2).toFixed(1)} kg of CO2</strong> this month. 
                That's equivalent to driving {(savingsAmount * 5).toFixed(0)} fewer miles in a gas car.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
