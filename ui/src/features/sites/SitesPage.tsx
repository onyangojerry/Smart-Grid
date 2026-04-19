import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { createSite, getSites } from "../../api/sites";
import { queryKeys } from "../../api/queryKeys";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { SiteForm } from "../../components/forms/SiteForm";
import "../../styles/features.css";

export function SitesPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [openCreate, setOpenCreate] = useState(false);

  const { scrollYProgress } = useScroll();
  const opacities = [
    useTransform(scrollYProgress, [0, 0.4], [1, 0]),
    useTransform(scrollYProgress, [0.4, 0.8], [0, 1]),
  ];

  const sitesQuery = useQuery({ queryKey: queryKeys.sites(), queryFn: getSites });
  const createMutation = useMutation({
    mutationFn: createSite,
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: queryKeys.sites() });
      setOpenCreate(false);
      navigate(`/sites/${created.id}`);
    }
  });

  if (sitesQuery.isLoading) return <LoadingSpinner />;
  if (sitesQuery.isError) return <ErrorBanner error={sitesQuery.error as Error} onRetry={() => sitesQuery.refetch()} />;

  const rows = sitesQuery.data || [];

  const images = [
    "https://images.unsplash.com/photo-1449156001931-82830078e073?auto=format&fit=crop&q=80&w=2000", // City/Grid Overview
    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&q=80&w=2000", // Office/Industrial Interior
  ];

  return (
    <div className="scrolly-container">
      <div className="scrolly-stage">
        {images.map((src, i) => (
          <motion.img key={src} src={src} className="stage-image" style={{ opacity: opacities[i] }} />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Your network of intelligence</div>
      </div>

      <div className="scrolly-story">
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">Active Sites</h1>
            <p className="story-subtitle">Managing the heartbeat of {rows.length} locations.</p>
            <p className="story-body">
              Every site represents a commitment to efficiency and sustainability. From residential homes to industrial hubs, your network is breathing with the grid.
            </p>
            <button 
              onClick={() => setOpenCreate((v) => !v)} 
              className="btn btn-lg btn-primary"
              style={{ marginTop: "2rem" }}
            >
              {openCreate ? "Back to Network" : "Add New Site"}
            </button>
          </motion.div>
        </section>

        <section className="story-section">
          <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
            {openCreate ? (
              <div style={{ background: "rgba(255,255,255,0.1)", padding: "3rem", borderRadius: "1rem", backdropFilter: "blur(20px)", maxWidth: "800px", margin: "0 auto" }}>
                <h2 className="story-title" style={{ fontSize: "2rem" }}>Integrate New Site</h2>
                <SiteForm onSubmit={(body) => createMutation.mutate(body)} loading={createMutation.isPending} />
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "2rem" }}>
                {rows.map((site: any) => (
                  <motion.div 
                    key={site.id}
                    whileHover={{ scale: 1.05 }}
                    style={{ 
                      background: "rgba(0,0,0,0.4)", 
                      padding: "2rem", 
                      borderRadius: "1rem", 
                      border: "1px solid rgba(255,255,255,0.1)",
                      backdropFilter: "blur(10px)",
                      cursor: "pointer"
                    }}
                    onClick={() => navigate(`/sites/${site.id}`)}
                  >
                    <h3 style={{ margin: 0, fontSize: "1.5rem", color: "var(--primary)" }}>{site.name}</h3>
                    <p style={{ opacity: 0.7, margin: "0.5rem 0" }}>{site.timezone}</p>
                    <div style={{ marginTop: "1.5rem", fontSize: "0.9rem" }}>
                      <strong>Reserve:</strong> {site.reserve_soc_min}% SoC<br/>
                      <strong>Created:</strong> {new Date(site.created_at).toLocaleDateString()}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
