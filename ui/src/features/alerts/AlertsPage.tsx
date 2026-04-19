import React, { useState, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { acknowledgeAlert, getAlertCounts, getAlerts, resolveAlert } from "../../api/alerts";
import { queryKeys } from "../../api/queryKeys";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { Badge } from "../../components/ui/Badge";
import "../../styles/features.css";

export function AlertsPage() {
  const { siteId } = useParams();
  const [stateFilter, setStateFilter] = useState<string>("");
  const qc = useQueryClient();

  const { scrollYProgress } = useScroll();
  const opacities = [
    useTransform(scrollYProgress, [0, 0.3], [1, 0]),
    useTransform(scrollYProgress, [0.3, 0.6], [0, 1]),
    useTransform(scrollYProgress, [0.6, 0.9], [0, 1]),
  ];

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

  const images = [
    "https://images.unsplash.com/photo-1590483736622-39da8caf3501?auto=format&fit=crop&q=80&w=2000", // Alert/Siren (Abstract)
    "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?auto=format&fit=crop&q=80&w=2000", // Blueprints/Warning
    "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?auto=format&fit=crop&q=80&w=2000", // Maintenance/Check
  ];

  return (
    <div className="scrolly-container">
      <div className="scrolly-stage">
        {images.map((src, i) => (
          <motion.img key={src} src={src} className="stage-image" style={{ opacity: opacities[i] }} />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Health Alerts Stream</div>
      </div>

      <div className="scrolly-story">
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">Health Alerts</h1>
            <p className="story-subtitle">The vigilance of SmartGrid for {siteId}</p>
            <p className="story-body">
              Our system never sleeps. We continuously monitor every register and communication channel to ensure your assets are operating within safe and efficient boundaries.
            </p>
          </motion.div>
        </section>

        {countsQuery.isSuccess && counts && (
          <section className="story-section">
            <div className="story-content-narrative">
              <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Site Health Summary</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "2rem", marginTop: "2rem" }}>
                <div style={{ borderLeft: "6px solid var(--error)", paddingLeft: "1.5rem" }}>
                  <span className="hero-label">Critical</span>
                  <span className="hero-metric" style={{ color: "var(--error)" }}>{counts.by_severity.critical}</span>
                </div>
                <div style={{ borderLeft: "6px solid var(--warning)", paddingLeft: "1.5rem" }}>
                  <span className="hero-label">Warning</span>
                  <span className="hero-metric" style={{ color: "var(--warning)" }}>{counts.by_severity.warning}</span>
                </div>
                <div style={{ borderLeft: "6px solid var(--primary)", paddingLeft: "1.5rem" }}>
                  <span className="hero-label">Info</span>
                  <span className="hero-metric" style={{ color: "var(--primary)" }}>{counts.by_severity.info}</span>
                </div>
                <div style={{ borderLeft: "6px solid white", paddingLeft: "1.5rem" }}>
                  <span className="hero-label">Total Open</span>
                  <span className="hero-metric" style={{ color: "white" }}>{counts.open}</span>
                </div>
              </div>
            </div>
          </section>
        )}

        <section className="story-section" style={{ minHeight: "150vh" }}>
          <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "2rem" }}>
              <div>
                <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Alert History</h2>
                <p className="story-subtitle">Detailed log of system notifications.</p>
              </div>
              <select 
                value={stateFilter} 
                onChange={(e) => setStateFilter(e.target.value)} 
                className="form-input"
                style={{ width: "auto", background: "rgba(255,255,255,0.1)", color: "white", border: "1px solid rgba(255,255,255,0.3)" }}
              >
                <option value="" style={{ background: "#111" }}>All Alerts</option>
                <option value="open" style={{ background: "#111" }}>Open</option>
                <option value="acknowledged" style={{ background: "#111" }}>Acknowledged</option>
                <option value="resolved" style={{ background: "#111" }}>Resolved</option>
              </select>
            </div>

            {alertsQuery.isLoading ? (
              <LoadingSpinner />
            ) : alertsQuery.isError ? (
              <div className="empty-state" style={{ color: "white" }}>
                <div className="empty-state-title">Unable to load alerts</div>
                <div className="empty-state-description">There was an error loading alerts.</div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                {(!alertsQuery.data?.items || alertsQuery.data.items.length === 0) ? (
                  <div className="empty-state" style={{ color: "white" }}>
                    <div className="empty-state-title">No alerts found</div>
                    <div className="empty-state-description">No alerts have been generated yet.</div>
                  </div>
                ) : (
                  alertsQuery.data.items.map((alert: any) => (
                    <motion.div
                      key={alert.id}
                      initial={{ opacity: 0, y: 10 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      style={{
                        background: alert.state === "open" ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.3)",
                        padding: "1.5rem",
                        borderRadius: "1rem",
                        backdropFilter: "blur(10px)",
                        borderLeft: `6px solid ${alert.severity === 'critical' ? 'var(--error)' : alert.severity === 'warning' ? 'var(--warning)' : 'var(--primary)'}`
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8, flexWrap: "wrap" }}>
                        <Badge kind="severity" value={alert.severity} />
                        <Badge kind="state" value={alert.state} />
                        <span style={{ fontWeight: 700, flex: 1, color: "white" }}>{alert.title}</span>
                        <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>
                          {new Date(alert.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div style={{ color: "rgba(255,255,255,0.8)", marginBottom: 12 }}>{alert.message}</div>
                      
                      {alert.state !== "resolved" && (
                        <div style={{ display: "flex", gap: 12 }}>
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
                    </motion.div>
                  ))
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
