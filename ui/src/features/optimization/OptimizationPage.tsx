import React, { useState, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { getOptimizationRuns, runOptimization, getOptimizationRunDetail } from "../../api/optimization";
import { queryKeys } from "../../api/queryKeys";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { OptimizationForm } from "../../components/forms/OptimizationForm";
import { ExplanationPanel } from "./ExplanationPanel";
import "../../styles/features.css";

export function OptimizationPage() {
  const { siteId } = useParams();
  const qc = useQueryClient();
  const [latestResultId, setLatestResultId] = useState<string | null>(null);
  
  const { scrollYProgress } = useScroll();

  const opacities = [
    useTransform(scrollYProgress, [0, 0.4], [1, 0]),
    useTransform(scrollYProgress, [0.4, 0.7], [0, 1]),
  ];

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const runsQuery = useQuery({
    queryKey: queryKeys.optimizationRuns(siteId),
    queryFn: () => getOptimizationRuns(siteId),
    refetchInterval: 60_000
  });

  const optimizationRunDetailQuery = useQuery({
    queryKey: queryKeys.optimizationRunDetail(latestResultId!),
    queryFn: () => getOptimizationRunDetail(latestResultId!),
    enabled: !!latestResultId,
  });

  const runMutation = useMutation({
    mutationFn: ({ siteId, body }: { siteId: string; body: any }) =>
      runOptimization(siteId, body),
    onSuccess: (result) => {
      const runId = result.optimization_run_id || result.id || null;
      setLatestResultId(runId);
      qc.invalidateQueries({ queryKey: queryKeys.optimizationRuns(siteId) });
      if (runId) qc.invalidateQueries({ queryKey: queryKeys.optimizationRunDetail(runId) });
    }
  });

  let currentExplanation = runMutation.data?.explanation || 
                           optimizationRunDetailQuery.data?.explanation || 
                           runMutation.data?.selected_action?.explanation || 
                           optimizationRunDetailQuery.data?.selected_action?.explanation;

  const images = [
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&q=80&w=2000", // CPU/Tech
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=2000", // Matrix/Digital
  ];

  return (
    <div className="scrolly-container">
      <div className="scrolly-stage">
        {images.map((src, i) => (
          <motion.img key={src} src={src} className="stage-image" style={{ opacity: opacities[i] }} />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Deep inside the logic</div>
      </div>

      <div className="scrolly-story">
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">The Silent Intelligence</h1>
            <p className="story-subtitle">Precision dispatch for {siteId}</p>
            <p className="story-body">
              Behind every watt saved is a thousand calculations. Our optimization engine balances battery health, grid pricing, and site demand in real-time.
            </p>
          </motion.div>
        </section>

        <section className="story-section">
          <div className="story-content-narrative">
            <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Manual Intervention</h2>
            <p className="story-body">
              While the system is autonomous, you can trigger a manual optimization run to see the logic in action or override current states.
            </p>
            <div style={{ background: "rgba(255,255,255,0.1)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
              <OptimizationForm onSubmit={(body) => runMutation.mutate({ siteId, body })} loading={runMutation.isPending} />
              {runMutation.isError && <ErrorBanner error={runMutation.error as Error} />}
              {currentExplanation && (
                <div style={{ marginTop: "2rem", borderTop: "1px solid rgba(255,255,255,0.2)", paddingTop: "1.5rem" }}>
                  <ExplanationPanel explanation={currentExplanation} />
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="story-section">
          <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
            <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Decision History</h2>
            <p className="story-subtitle">The paper trail of intelligent choices.</p>
            
            <div style={{ display: "grid", gap: "1rem", marginTop: "2rem" }}>
              {runsQuery.isLoading ? <LoadingSpinner /> : (runsQuery.data || []).slice(0, 10).map((run: any) => (
                <motion.div 
                  key={run.id} 
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  style={{ 
                    background: "rgba(0,0,0,0.3)", 
                    padding: "1.5rem", 
                    borderRadius: "0.5rem", 
                    borderLeft: "4px solid var(--primary)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center"
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>{run.explanation?.decision || run.selected_action?.command_type || "No Decision"}</div>
                    <div style={{ opacity: 0.7, fontSize: "0.9rem" }}>{run.explanation?.summary || run.selected_action?.explanation?.summary || "Automatic run completed"}</div>
                  </div>
                  <div style={{ opacity: 0.5, fontSize: "0.8rem", textAlign: "right" }}>
                    Mode: {run.mode}<br/>
                    {new Date(run.ts || Date.now()).toLocaleTimeString()}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
