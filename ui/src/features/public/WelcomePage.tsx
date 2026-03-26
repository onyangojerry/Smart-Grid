import React from "react";
import { useNavigate } from "react-router-dom";
import { Topbar } from "../../components/layout/Topbar";
import "../../styles/welcome.css";

export function WelcomePage() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Topbar />
      
      <main className="welcome-main">
        {/* Hero Section */}
        <section className="hero-section">
          <h1 className="hero-title">
            The Intelligent <span className="hero-title-accent">Energy</span> Control Loop
          </h1>
          <p className="hero-subtitle">
            Autonomous optimization, real-time telemetry ingestion, and industrial-grade reliability for your distributed energy resources.
          </p>
          <div className="hero-actions">
            <button 
              onClick={() => navigate("/signup")}
              className="btn-primary"
            >
              Get Started
            </button>
            <button 
              onClick={() => navigate("/login")}
              className="btn-secondary"
            >
              Operator Login
            </button>
          </div>
        </section>

        {/* Feature Grid */}
        <section className="feature-grid">
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3 className="feature-title">Unified Telemetry</h3>
            <p className="feature-text">
              Ingest real-time points from PV, Load, and Battery systems. High-frequency monitoring with built-in deduplication and state reconstruction.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🧠</div>
            <h3 className="feature-title">Rule-Based Logic</h3>
            <p className="feature-text">
              Custom scoring functions evaluate candidate actions against energy costs, battery health, and grid constraints for optimal dispatch.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🛡️</div>
            <h3 className="feature-title">Industrial Safety</h3>
            <p className="feature-text">
              Built-in safe modes for connectivity loss or thermal excursions. Hard constraints ensure hardware operates within manufacturer specifications.
            </p>
          </div>
        </section>

        {/* Technical Overview */}
        <section className="technical-section">
          <h2 className="technical-title">Operational Flow</h2>
          <div className="technical-grid">
            {[
              { step: "01", title: "Ingestion", desc: "Telemtry streams resolve via Site repository." },
              { step: "02", title: "State Sync", desc: "Build comprehensive SiteState across all assets." },
              { step: "03", title: "Evaluation", desc: "Rule Engine computes ScoreBreakdown for actions." },
              { step: "04", title: "Dispatch", desc: "Commands sent to edge gateway with retry logic." }
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
        &copy; {new Date().getFullYear()} SmartGrid — EMS Operational Console
      </footer>
    </div>
  );
}
