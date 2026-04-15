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
            Your home, <span className="hero-title-accent">breathing</span> with the grid.
          </h1>
          <p className="hero-subtitle">
            While you sleep, our silent intelligence is working to lower your bills and protect the planet. Experience the magic of autonomous energy.
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
              Member Login
            </button>
          </div>
        </section>

        {/* Story Grid */}
        <section className="feature-grid">
          <div className="feature-card">
            <div className="feature-icon">🌿</div>
            <h3 className="feature-title">Eco-Intelligence</h3>
            <p className="feature-text">
              We don't just move electrons; we optimize for a greener future. Our algorithms prioritize clean energy when the sun is shining.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">💰</div>
            <h3 className="feature-title">Silent Savings</h3>
            <p className="feature-text">
              Our system tracks market prices in real-time, automatically shifting your usage to avoid expensive peak rates without you lifting a finger.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🛡️</div>
            <h3 className="feature-title">Total Peace of Mind</h3>
            <p className="feature-text">
              Industrial-grade safety meets home comfort. Your hardware is protected by smart constraints that ensure long-lasting battery health.
            </p>
          </div>
        </section>

        {/* The "How it Works" Story */}
        <section className="technical-section">
          <h2 className="technical-title">The Journey of a Smart Electron</h2>
          <div className="technical-grid">
            {[
              { step: "01", title: "Listen", desc: "We listen to your home's heartbeat—PV, battery, and load." },
              { step: "02", title: "Analyze", desc: "Our AI weighs thousands of possibilities to find your best path." },
              { step: "03", title: "Act", desc: "We gently guide your system to store or use energy at the perfect time." },
              { step: "04", title: "Impact", desc: "You wake up to lower costs and a smaller carbon footprint." }
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
