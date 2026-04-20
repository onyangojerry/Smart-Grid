import React, { useState, useMemo } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useParams, useSearchParams } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { runSimulation, getSimulationDetail } from "../../api/simulation";
import { queryKeys } from "../../api/queryKeys";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { SimulationForm } from "../../components/forms/SimulationForm";
import { ActionHistoryChart } from "../../components/charts/ActionHistoryChart";
import "../../styles/features.css";

export function SimulationPage() {
  const { siteId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const simId = searchParams.get("simId");
  const [latestResult, setLatestResult] = useState<any>(null);

  const { scrollYProgress } = useScroll();

  const opacities = [
    useTransform(scrollYProgress, [0, 0.3], [1, 0]),
    useTransform(scrollYProgress, [0.3, 0.6], [0, 1]),
    useTransform(scrollYProgress, [0.6, 0.8], [0, 1]),
  ];

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const detailQuery = useQuery({
    queryKey: queryKeys.simulation(siteId, simId!),
    queryFn: () => getSimulationDetail(siteId, simId!),
    enabled: !!simId
  });

  const mutation = useMutation({
    mutationFn: ({ siteId, body }: { siteId: string; body: any }) =>
      runSimulation(siteId, body),
    onSuccess: (result) => {
      setLatestResult(result);
      if (result.id) setSearchParams({ simId: result.id });
    }
  });

  const displayResult = latestResult || detailQuery.data;

  const images = [
    "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?auto=format&fit=crop&q=80&w=2000", // Future/Sunrise
    "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?auto=format&fit=crop&q=80&w=2000", // Blueprints/Planning
    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=2000", // Complex Data Chart
  ];

  return (
    <div className="scrolly-container">
      <div className="scrolly-stage">
        {images.map((src, i) => (
          <motion.img key={src} src={src} className="stage-image" style={{ opacity: opacities[Math.min(i, opacities.length - 1)] }} />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Simulate your future</div>
      </div>

      <div className="scrolly-story">
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">Future Vision</h1>
            <p className="story-subtitle">Projecting the impact of smart energy for {siteId}</p>
            <p className="story-body">
              Don't leave your energy strategy to chance. Simulate complex scenarios—from extreme weather to market volatility—and see how our logic protects your assets.
            </p>
          </motion.div>
        </section>

        <section className="story-section">
          <div className="story-content-narrative">
            <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Scenario Modeling</h2>
            <div style={{ background: "rgba(255,255,255,0.1)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
              <SimulationForm onSubmit={(body) => mutation.mutate({ siteId, body })} loading={mutation.isPending} />
              {mutation.isError && <ErrorBanner error={mutation.error as Error} />}
            </div>
          </div>
        </section>

        {displayResult && (
          <>
            <section className="story-section right">
              <div className="story-content-narrative">
                <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Projected Outcomes</h2>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
                  <div>
                    <span className="hero-label">Savings</span>
                    <span className="hero-metric">{displayResult.savings_percent.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="hero-label">Cost Reduction</span>
                    <span className="hero-metric">${(displayResult.baseline_cost - displayResult.optimized_cost).toFixed(0)}</span>
                  </div>
                </div>
                <p className="story-body" style={{ marginTop: "2rem" }}>
                  Baseline cost: ${displayResult.baseline_cost.toFixed(2)} vs Optimized: ${displayResult.optimized_cost.toFixed(2)}
                </p>
              </div>
            </section>

            <section className="story-section" style={{ padding: "0 2%" }}>
              <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
                <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Action History Map</h2>
                <div style={{ background: "rgba(0,0,0,0.4)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
                  <ActionHistoryChart
                    points={displayResult.action_history.map((a: any, idx: number) => ({
                      ts: String(idx),
                      action: a.action,
                      target_power_kw: a.target_power_kw,
                      score: 0
                    }))}
                  />
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
