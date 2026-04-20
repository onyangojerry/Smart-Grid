import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { getTelemetryHistory, getTelemetryLatest } from "../../api/telemetry";
import { queryKeys } from "../../api/queryKeys";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { TelemetryLineChart } from "../../components/charts/TelemetryLineChart";
import "../../styles/features.css";

export function TelemetryPage() {
  const { siteId } = useParams();
  const [selectedKey, setSelectedKey] = useState("battery_soc");
  const to = useMemo(() => new Date().toISOString(), []);
  const from = useMemo(() => new Date(Date.now() - 24 * 3600 * 1000).toISOString(), []);

  const { scrollYProgress } = useScroll();

  // Map scroll progress to stage
  const opacities = [
    useTransform(scrollYProgress, [0, 0.3], [1, 0]),
    useTransform(scrollYProgress, [0.3, 0.5, 0.7], [0, 1, 0]),
    useTransform(scrollYProgress, [0.7, 0.9], [0, 1]),
  ];

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const latestQuery = useQuery({ 
    queryKey: queryKeys.telemetryLatest(siteId), 
    queryFn: () => getTelemetryLatest(siteId) 
  });
  
  const historyQuery = useQuery({
    queryKey: queryKeys.telemetryHistory(siteId, selectedKey),
    queryFn: () => getTelemetryHistory(siteId, selectedKey, from, to)
  });

  if (latestQuery.isLoading) return <LoadingSpinner />;
  if (latestQuery.isError) return <ErrorBanner error={latestQuery.error as Error} />;

  const latest = latestQuery.data || {};
  const keys = Object.keys(latest);

  const images = [
    "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&q=80&w=2000", // Charging Station/Tech
    "https://images.unsplash.com/photo-1558449028-b53a39d100fc?auto=format&fit=crop&q=80&w=2000", // Industrial Battery Setup
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80&w=2000", // Abstract Data/Digital Flow
  ];

  return (
    <div className="scrolly-container">
      {/* THE STAGE */}
      <div className="scrolly-stage">
        {images.map((src, i) => (
          <motion.img
            key={src}
            src={src}
            className="stage-image"
            style={{ opacity: opacities[i] }}
          />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Explore your site's heartbeat</div>
      </div>

      {/* THE STORY */}
      <div className="scrolly-story">
        
        {/* Intro */}
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">The Pulse of Power</h1>
            <p className="story-subtitle">Real-time vitality for site: {siteId}</p>
          </motion.div>
        </section>

        {/* Real-time Vitals */}
        <section className="story-section">
          <div className="story-content-narrative">
            <h2 className="story-title" style={{ fontSize: "2.5rem" }}>System Vitality</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginTop: "2rem" }}>
              {Object.entries(latest).map(([key, point]) => (
                <motion.div 
                  key={key}
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  style={{ borderLeft: "4px solid var(--primary)", paddingLeft: "1rem" }}
                >
                  <span className="hero-label" style={{ fontSize: "0.8rem" }}>{key}</span>
                  <span className="hero-metric" style={{ fontSize: "3rem" }}>
                    {point.value} <span style={{ fontSize: "1.5rem", opacity: 0.6 }}>{point.unit}</span>
                  </span>
                </motion.div>
              ))}
            </div>
            <p className="story-body" style={{ marginTop: "2rem" }}>
              Every heartbeat is captured. These values represent the current state of your energy ecosystem, monitored every second.
            </p>
          </div>
        </section>

        {/* Historical Context */}
        <section className="story-section" style={{ padding: "0 2%" }}>
          <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "2rem" }}>
              <div>
                <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Historical Rhythm</h2>
                <p className="story-subtitle">Tracking the ebb and flow over 24 hours.</p>
              </div>
              <select 
                value={selectedKey} 
                onChange={(e) => setSelectedKey(e.target.value)} 
                className="form-input"
                style={{ width: "auto", background: "rgba(255,255,255,0.1)", color: "white", border: "1px solid rgba(255,255,255,0.3)" }}
              >
                {keys.map((k) => (
                  <option key={k} value={k} style={{ background: "#111" }}>{k}</option>
                ))}
              </select>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
              {historyQuery.isLoading ? (
                <LoadingSpinner />
              ) : historyQuery.isError ? (
                <ErrorBanner error={historyQuery.error as Error} />
              ) : (
                <TelemetryLineChart points={(historyQuery.data || []).map((p) => ({ ts: p.ts, value: p.value }))} />
              )}
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
