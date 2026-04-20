import React, { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { getSavingsSummary } from "../../api/savings";
import { queryKeys } from "../../api/queryKeys";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import "../../styles/features.css";

export function SavingsPage() {
  const { siteId } = useParams();
  const to = useMemo(() => new Date().toISOString(), []);
  const from = useMemo(() => new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(), []);
  
  const { scrollYProgress } = useScroll();

  // Map scroll progress to image opacities
  const opacities = [
    useTransform(scrollYProgress, [0, 0.15], [1, 0]),
    useTransform(scrollYProgress, [0.15, 0.25, 0.4], [0, 1, 0]),
    useTransform(scrollYProgress, [0.4, 0.5, 0.65], [0, 1, 0]),
    useTransform(scrollYProgress, [0.65, 0.75, 0.85], [0, 1, 0]),
    useTransform(scrollYProgress, [0.85, 0.95], [0, 1]),
  ];

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const query = useQuery({ 
    queryKey: queryKeys.savings(siteId), 
    queryFn: () => getSavingsSummary(siteId, from, to) 
  });

  if (query.isLoading) return <LoadingSpinner />;
  if (query.isError) return <ErrorBanner error={query.error as Error} onRetry={() => query.refetch()} />;
  if (!query.data) return <ErrorBanner error={new Error("No savings data returned")} onRetry={() => query.refetch()} />;

  const data = query.data;
  const savingsAmount = data.baseline_cost - data.optimized_cost;

  const images = [
    "https://images.unsplash.com/photo-1513828583688-c52646db42da?auto=format&fit=crop&q=80&w=2000", // Sustainable Facility
    "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&q=80&w=2000", // The Grid/Cables
    "https://images.unsplash.com/photo-1569163139599-0f4517e36f51?auto=format&fit=crop&q=80&w=2000", // Battery/Tech
    "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&q=80&w=2000", // Money/Success (Calculator/Hand)
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&q=80&w=2000", // Forest/CO2
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
            style={{ opacity: opacities[Math.min(i, opacities.length - 1)] }}
          />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Scroll to discover the impact</div>
      </div>

      {/* THE STORY */}
      <div className="scrolly-story">
        
        {/* Intro Section */}
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">Financial Impact</h1>
            <p className="story-subtitle">Seeing the fruits of your smart energy decisions.</p>
          </motion.div>
        </section>

        {/* Baseline Section */}
        <section className="story-section">
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="story-content-narrative"
          >
            <span className="hero-label">Potential Spending</span>
            <span className="hero-metric">${data.baseline_cost.toFixed(2)}</span>
            <p className="story-body">
              This is what you would have spent without SmartGrid optimization. 
              By relying purely on the grid, your facility would have been subject to the full weight of peak pricing and inefficiency.
            </p>
          </motion.div>
        </section>

        {/* Intervention Section */}
        <section className="story-section right">
          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="story-content-narrative"
          >
            <span className="hero-label">Actual Spending</span>
            <span className="hero-metric">${data.optimized_cost.toFixed(2)}</span>
            <p className="story-body" style={{ color: "var(--primary)", fontWeight: 800 }}>
              Reduced by {data.savings_percent.toFixed(1)}%
            </p>
            <p className="story-body">
              Every time our AI makes a decision to charge your battery during low-price periods or discharge it when prices spike, we record the difference. 
            </p>
          </motion.div>
        </section>

        {/* The Big Save */}
        <section className="story-section center">
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            transition={{ duration: 1, type: "spring" }}
            className="story-content-narrative"
          >
            <span className="hero-label">Money Kept</span>
            <span className="hero-metric" style={{ color: "#4ade80" }}>${savingsAmount.toFixed(2)}</span>
            <p className="story-body">
              Back in your pocket. This isn't just a number; it's capital returned to your home or business, earned through silent intelligence.
            </p>
          </motion.div>
        </section>

        {/* Sustainability Section */}
        <section className="story-section">
          <motion.div 
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="story-content-narrative"
          >
            <h2 className="story-title" style={{ fontSize: "3rem" }}>Positive Footprint</h2>
            <p className="story-body">
              Cleaner Energy usage. By shifting your load to solar hours, you've avoided using approximately <strong>{(savingsAmount * 1.2).toFixed(1)} kg of CO2</strong> this month.
            </p>
            <p className="story-body" style={{ fontStyle: "italic", opacity: 0.8 }}>
              That's equivalent to driving {(savingsAmount * 5).toFixed(0)} fewer miles in a gas car.
            </p>
          </motion.div>
        </section>

      </div>
    </div>
  );
}
