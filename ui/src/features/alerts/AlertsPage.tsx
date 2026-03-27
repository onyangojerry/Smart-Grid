import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { acknowledgeAlert, getAlertCounts, getAlerts, resolveAlert } from "../../api/alerts";
import { queryKeys } from "../../api/queryKeys";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { Badge } from "../../components/ui/Badge";
import "../../styles/features.css";

export function AlertsPage() {
  const { siteId } = useParams();
  const [stateFilter, setStateFilter] = useState<string>("");
  const qc = useQueryClient();

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const alertsQuery = useQuery({
    queryKey: queryKeys.alerts(siteId),
    queryFn: () => getAlerts(siteId, stateFilter || undefined),
    refetchInterval: 30_000
  });

  const countsQuery = useQuery({
    queryKey: queryKeys.alertCounts(siteId),
    queryFn: () => getAlertCounts(siteId),
    refetchInterval: 60_000
  });

  const ackMutation = useMutation({
    mutationFn: acknowledgeAlert,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.alerts(siteId) });
      qc.invalidateQueries({ queryKey: queryKeys.alertCounts(siteId) });
    }
  });

  const resolveMutation = useMutation({
    mutationFn: resolveAlert,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.alerts(siteId) });
      qc.invalidateQueries({ queryKey: queryKeys.alertCounts(siteId) });
    }
  });

  const counts = countsQuery.data;

  return (
    <div className="page-content">
      <PageHeader title="Alerts" subtitle={siteId} />
      
      {countsQuery.isSuccess && counts && (
        <div className="stats-grid" style={{ marginBottom: 16 }}>
          <div className="stat-card" style={{ background: "var(--error-bg, rgba(211, 47, 47, 0.1))", borderColor: "var(--error)" }}>
            <div className="stat-label">Open Critical</div>
            <div className="stat-value" style={{ color: "var(--error)" }}>{counts.by_severity.critical}</div>
          </div>
          <div className="stat-card" style={{ background: "rgba(245, 124, 0, 0.1)", borderColor: "var(--warning)" }}>
            <div className="stat-label">Open Warnings</div>
            <div className="stat-value" style={{ color: "var(--warning)" }}>{counts.by_severity.warning}</div>
          </div>
          <div className="stat-card" style={{ background: "rgba(13, 71, 161, 0.1)", borderColor: "var(--primary)" }}>
            <div className="stat-label">Open Info</div>
            <div className="stat-value" style={{ color: "var(--primary)" }}>{counts.by_severity.info}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Open</div>
            <div className="stat-value">{counts.open}</div>
          </div>
        </div>
      )}

      <Card title="Alert history">
        <div style={{ marginBottom: 16 }}>
          <select value={stateFilter} onChange={(e) => setStateFilter(e.target.value)} className="form-input">
            <option value="">All Alerts</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
        {alertsQuery.isLoading ? (
          <LoadingSpinner />
        ) : alertsQuery.isError ? (
          <div className="empty-state">
            <div className="empty-state-title">Unable to load alerts</div>
            <div className="empty-state-description">
              There was an error loading alerts. This may be because the alerts table hasn't been set up yet.
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {(!alertsQuery.data?.items || alertsQuery.data.items.length === 0) ? (
              <div className="empty-state">
                <div className="empty-state-title">No alerts found</div>
                <div className="empty-state-description">
                  {stateFilter ? `No ${stateFilter} alerts at this time.` : "No alerts have been generated yet."}
                </div>
              </div>
            ) : (
              alertsQuery.data.items.map((alert) => (
                <div
                  key={alert.id}
                  className="card"
                  style={{
                    background: alert.state === "open" ? "var(--card-bg)" : "var(--bg)"
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
                    <Badge kind="severity" value={alert.severity} />
                    <Badge kind="state" value={alert.state} />
                    <span style={{ fontWeight: 600, flex: 1 }}>{alert.title}</span>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ color: "var(--text)", marginBottom: 8 }}>{alert.message}</div>
                  {alert.source_key && (
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Source: {alert.source_key}</div>
                  )}
                  {alert.state !== "resolved" && (
                    <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                      {alert.state === "open" && (
                        <button
                          onClick={() => ackMutation.mutate(alert.id)}
                          className="btn btn-secondary btn-sm"
                        >
                          Acknowledge
                        </button>
                      )}
                      <button
                        onClick={() => resolveMutation.mutate(alert.id)}
                        className="btn btn-success btn-sm"
                      >
                        Resolve
                      </button>
                    </div>
                  )}
                  {(alert.acknowledged_at || alert.resolved_at) && (
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
                      {alert.acknowledged_at && `Acknowledged: ${new Date(alert.acknowledged_at).toLocaleString()}`}
                      {alert.acknowledged_at && alert.resolved_at && " | "}
                      {alert.resolved_at && `Resolved: ${new Date(alert.resolved_at).toLocaleString()}`}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
