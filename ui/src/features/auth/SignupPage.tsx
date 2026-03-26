import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { useAuth } from "./useAuth";
import "../../styles/auth.css";

export function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">Create Account</h2>
        <form
          className="auth-form"
          onSubmit={async (e) => {
            e.preventDefault();
            setError(null);
            setLoading(true);
            try {
              await signup(email, password, name);
              navigate("/sites", { replace: true });
            } catch (err) {
              setError(err as Error);
            } finally {
              setLoading(false);
            }
          }}
        >
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input
              className="form-input"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          <button className="auth-button" disabled={loading} type="submit">
            {loading ? "Creating account..." : "Sign up"}
          </button>
          <div className="auth-footer">
            Already have an account? <Link to="/login">Login</Link>
          </div>
          <ErrorBanner error={error} />
        </form>
      </div>
    </div>
  );
}
