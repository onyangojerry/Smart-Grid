import React from "react";
import { useNavigate } from "react-router-dom";
import { Topbar } from "../../components/layout/Topbar";
import "../../styles/welcome.css";

export function WelcomePage() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--bg)" }}>
      <Topbar />
      
      <main className="welcome-main">
        {/* Hero Section */}
        <section className="hero-section">
          <h1 className="hero-title">
            Your energy, <span className="hero-title-accent">breathing</span> with the grid.
          </h1>
          <p className="hero-subtitle">
            Whether a smart home or an industrial facility, our silent intelligence works to lower your costs and protect the planet. Experience the power of autonomous energy management.
          </p>
          <div className="hero-actions">
            <button 
              onClick={() => navigate("/signup")}
              className="btn btn-primary btn-lg"
            >
              Start Saving Today
            </button>
            <button 
              onClick={() => navigate("/login")}
              className="btn btn-secondary btn-lg"
            >
              Operator Login
            </button>
          </div>
        </section>

        {/* Story Grid */}
        <section className="feature-grid">
          <div className="feature-card">
            <div className="feature-icon">🌿</div>
            <h3 className="feature-title">Impact-First Intelligence</h3>
            <p className="feature-text">
              We don't just move electrons; we optimize for a greener future. Our algorithms prioritize clean energy and system health, whether at home or in industry.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3 className="feature-title">Precision Savings</h3>
            <p className="feature-text">
              Our system tracks market prices in real-time, automatically shifting loads to avoid expensive peak rates and maximizing your ROI without any manual effort.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🛡️</div>
            <h3 className="feature-title">Industrial-Grade Safety</h3>
            <p className="feature-text">
              Advanced reliability meets operational comfort. Your hardware is protected by smart constraints that ensure long-lasting battery health and uptime.
            </p>
          </div>
        </section>

        {/* The "How it Works" Story */}
        <section className="technical-section">
          <h2 className="technical-title">The Journey of Smart Energy</h2>
          <div className="technical-grid">
            {[
              { step: "01", title: "Monitor", desc: "We ingest your system's heartbeat—PV, battery, and load—at high frequency." },
              { step: "02", title: "Analyze", desc: "Our AI evaluates thousands of possibilities to find your most efficient path." },
              { step: "03", title: "Act", desc: "We gently guide your assets to store or dispatch energy at the optimal time." },
              { step: "04", title: "Impact", desc: "You achieve lower costs, reduced peak demand, and a smaller carbon footprint." }
            ].map((s) => (
              <div key={s.step} className="step-container">
                <div className="step-number">{s.step}</div>
                <div className="step-title">{s.title}</div>
                <div className="step-text">{s.desc}</div>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="welcome-footer">
        &copy; {new Date().getFullYear()} SmartGrid — Built for a Sustainable Future.
      </footer>
    </div>
  );
}
