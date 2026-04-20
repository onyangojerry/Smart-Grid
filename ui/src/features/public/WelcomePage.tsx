import React from "react";
import { useNavigate } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { Topbar } from "../../components/layout/Topbar";
import "../../styles/features.css";
import "../../styles/welcome.css";

export function WelcomePage() {
  const navigate = useNavigate();
  const { scrollYProgress } = useScroll();

  // Multi-stage opacities for a long narrative
  const opacities = [
    useTransform(scrollYProgress, [0, 0.1], [1, 0]),           // Hero
    useTransform(scrollYProgress, [0.1, 0.2, 0.3], [0, 1, 0]), // Impact
    useTransform(scrollYProgress, [0.3, 0.4, 0.5], [0, 1, 0]), // Savings
    useTransform(scrollYProgress, [0.5, 0.6, 0.7], [0, 1, 0]), // Safety
    useTransform(scrollYProgress, [0.7, 0.8, 0.9], [0, 1, 0]), // Technical Journey
    useTransform(scrollYProgress, [0.9, 1.0], [0, 1]),         // Footer/CTA
  ];

  const images = [
    "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&q=80&w=2000", // Hero: Grid/Cables
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&q=80&w=2000", // Impact: Forest
    "https://images.unsplash.com/photo-1554224155-169641357599?auto=format&fit=crop&q=80&w=2000", // Savings: Calculator/Money
    "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&q=80&w=2000", // Safety: Industrial/Tech
    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=2000", // Journey: Data/Logic
    "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?auto=format&fit=crop&q=80&w=2000", // CTA: Sunrise/Future
  ];

  return (
    <div className="scrolly-container" style={{ background: "#0f172a" }}>
      <Topbar />

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
        <div className="scroll-hint">Scroll to begin the story</div>
      </div>

      {/* THE STORY */}
      <div className="scrolly-story">
        
        {/* Hero Section */}
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <span className="hero-label" style={{ marginBottom: "1rem", display: "block", color: "var(--primary)" }}>Welcome to SmartGrid</span>
            <h1 className="story-title">
              Your energy, <span style={{ color: "var(--primary)", fontStyle: "italic" }}>breathing</span> with the grid.
            </h1>
            <p className="story-subtitle">
              Whether a smart home or an industrial facility, our silent intelligence works to lower your costs and protect the planet.
            </p>
            <div style={{ display: "flex", gap: "1rem", justifyContent: "center", marginTop: "2rem" }}>
              <button onClick={() => navigate("/signup")} className="btn btn-primary btn-lg">Start Saving Today</button>
              <button onClick={() => navigate("/login")} className="btn btn-secondary btn-lg">Operator Login</button>
            </div>
          </motion.div>
        </section>

        {/* Impact Section */}
        <section className="story-section">
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            className="story-content-narrative"
          >
            <span className="hero-label">🌿 01. Impact-First</span>
            <h2 className="story-title" style={{ fontSize: "3rem" }}>Intelligence with Purpose</h2>
            <p className="story-body">
              We don't just move electrons; we optimize for a greener future. Our algorithms prioritize clean energy and system health, ensuring that every watt used contributes to a sustainable legacy.
            </p>
          </motion.div>
        </section>

        {/* Savings Section */}
        <section className="story-section right">
          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            className="story-content-narrative"
          >
            <span className="hero-label">📊 02. Precision</span>
            <h2 className="story-title" style={{ fontSize: "3rem" }}>Savings at Scale</h2>
            <p className="story-body">
              Our system tracks market prices in real-time, automatically shifting loads to avoid expensive peak rates and maximizing your ROI without any manual effort.
            </p>
          </motion.div>
        </section>

        {/* Safety Section */}
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            className="story-content-narrative"
          >
            <span className="hero-label">🛡️ 03. Reliability</span>
            <h2 className="story-title" style={{ fontSize: "3rem" }}>Industrial-Grade Safety</h2>
            <p className="story-body">
              Advanced reliability meets operational comfort. Your hardware is protected by smart constraints that ensure long-lasting battery health and uptime.
            </p>
          </motion.div>
        </section>

        {/* Technical Journey Section */}
        <section className="story-section" style={{ padding: "0 5%" }}>
          <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
            <h2 className="story-title" style={{ fontSize: "3.5rem", textAlign: "center", marginBottom: "4rem" }}>The Journey of Smart Energy</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "3rem" }}>
              {[
                { step: "01", title: "Monitor", desc: "We ingest your system's heartbeat—PV, battery, and load—at high frequency." },
                { step: "02", title: "Analyze", desc: "Our AI evaluates thousands of possibilities to find your most efficient path." },
                { step: "03", title: "Act", desc: "We gently guide your assets to store or dispatch energy at the optimal time." },
                { step: "04", title: "Impact", desc: "You achieve lower costs, reduced peak demand, and a smaller carbon footprint." }
              ].map((s) => (
                <motion.div 
                  key={s.step}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  style={{ borderLeft: "2px solid var(--primary)", paddingLeft: "1.5rem" }}
                >
                  <div style={{ color: "var(--primary)", fontWeight: 800, fontFamily: "var(--font-mono)", marginBottom: "0.5rem" }}>{s.step}</div>
                  <h3 style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>{s.title}</h3>
                  <p style={{ opacity: 0.8, lineHeight: "1.6" }}>{s.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Footer/CTA Section */}
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            className="story-content-narrative"
          >
            <h2 className="story-title">Join the Evolution</h2>
            <p className="story-body">
              Ready to transform your energy profile? Join hundreds of homes and facilities already breathing with the grid.
            </p>
            <div style={{ display: "flex", gap: "1rem", justifyContent: "center", marginTop: "3rem" }}>
              <button onClick={() => navigate("/signup")} className="btn btn-primary btn-lg">Get Started</button>
            </div>
            <footer style={{ marginTop: "6rem", opacity: 0.5, fontSize: "0.9rem" }}>
              &copy; {new Date().getFullYear()} SmartGrid — Built for a Sustainable Future.
            </footer>
          </motion.div>
        </section>

      </div>
    </div>
  );
}
