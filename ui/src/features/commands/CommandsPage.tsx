import React, { useState, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { acknowledgeCommand, listCommands } from "../../api/commands";
import { queryKeys } from "../../api/queryKeys";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { DataTable } from "../../components/tables/DataTable";
import { Badge } from "../../components/ui/Badge";
import "../../styles/features.css";

export function CommandsPage() {
  const { siteId } = useParams();
  const [statusFilter, setStatusFilter] = useState("");
  const qc = useQueryClient();

  const { scrollYProgress } = useScroll();
  const opacities = [
    useTransform(scrollYProgress, [0, 0.4], [1, 0]),
    useTransform(scrollYProgress, [0.4, 0.8], [0, 1]),
  ];

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const commandsQuery = useQuery({
    queryKey: queryKeys.commands(siteId),
    queryFn: () => listCommands(siteId, statusFilter || undefined),
    refetchInterval: 30_000
  });

  const ackMutation = useMutation({
    mutationFn: acknowledgeCommand,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.commands(siteId) });
    }
  });

  const images = [
    "https://images.unsplash.com/photo-1558494949-ef010cbdcc51?auto=format&fit=crop&q=80&w=2000", // Server/Tech
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&q=80&w=2000", // CPU/Tech
  ];

  return (
    <div className="scrolly-container">
      <div className="scrolly-stage">
        {images.map((src, i) => (
          <motion.img key={src} src={src} className="stage-image" style={{ opacity: opacities[i] }} />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Precision Dispatch Stream</div>
      </div>

      <div className="scrolly-story">
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">Precision Dispatch</h1>
            <p className="story-subtitle">The command lineage for {siteId}</p>
            <p className="story-body">
              Every watt moved is the result of a precise digital handshake. This stream represents the active dialogue between our cloud intelligence and your edge gateway.
            </p>
          </motion.div>
        </section>

        <section className="story-section">
          <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "2rem" }}>
              <div>
                <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Command Stream</h2>
                <p className="story-subtitle">Real-time status of dispatched instructions.</p>
              </div>
              <select 
                value={statusFilter} 
                onChange={(e) => setStatusFilter(e.target.value)} 
                className="form-input"
                style={{ width: "auto", background: "rgba(255,255,255,0.1)", color: "white", border: "1px solid rgba(255,255,255,0.3)" }}
              >
                <option value="" style={{ background: "#111" }}>all</option>
                <option value="queued" style={{ background: "#111" }}>queued</option>
                <option value="sent" style={{ background: "#111" }}>sent</option>
                <option value="acked" style={{ background: "#111" }}>acknowledged</option>
                <option value="failed" style={{ background: "#111" }}>failed</option>
              </select>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
              {commandsQuery.isLoading ? (
                <LoadingSpinner />
              ) : commandsQuery.isError ? (
                <ErrorBanner error={commandsQuery.error as Error} />
              ) : (
                <DataTable
                  rows={commandsQuery.data || []}
                  getRowKey={(r) => r.id}
                  columns={[
                    { key: "requested", header: "Requested At", render: (r) => <span style={{ color: "white" }}>{r.requested_at}</span> },
                    { key: "type", header: "Command Type", render: (r) => <Badge kind="plain" value={r.command_type} /> },
                    { key: "status", header: "Status", render: (r) => <Badge kind="command" value={r.status === "acked" ? "acknowledged" : r.status} /> },
                    {
                      key: "failure",
                      header: "Failure Reason",
                      render: (r) => (r.failure_reason ? <span style={{ color: "var(--error)" }}>{r.failure_reason}</span> : "—")
                    },
                    {
                      key: "ack",
                      header: "",
                      render: (r) =>
                        r.status === "sent" || r.status === "queued" ? (
                          <button 
                            onClick={() => ackMutation.mutate(r.id)} 
                            className="btn btn-sm btn-primary"
                            style={{ width: "auto" }}
                          >
                            Acknowledge
                          </button>
                        ) : null
                    }
                  ]}
                />
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
