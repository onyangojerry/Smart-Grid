import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/useAuth";
import { useTheme } from "../../hooks/useTheme";

export function Topbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();

  return (
    <header className="topbar">
      <div className="topbar-left">
        <Link to="/" className="topbar-logo">
          {/* <span className="topbar-logo-icon">⚡</span> */}
          <strong className="topbar-logo-text">SmartGrid</strong>
        </Link>
      </div>

      <div className="topbar-right">
        <div className="theme-switcher">
          {(["light", "dark", "industrial"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTheme(t)}
              className={theme === t ? "theme-button active" : "theme-button"}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>

        <div className="auth-nav">
          {!isAuthenticated ? (
            <>
              <button onClick={() => navigate("/login")} className="login-link-btn">
                Login
              </button>
              <button onClick={() => navigate("/signup")} className="signup-btn">
                Sign Up
              </button>
            </>
          ) : (
            <div className="user-profile-container">
              <div className="user-avatar-trigger">
                <img
                  src={`https://picsum.photos/seed/${user?.id}/32/32`}
                  alt={user?.full_name || "User"}
                  className="user-avatar-img"
                />
                <div className="user-dropdown">
                  <div className="user-dropdown-info">
                    <div className="user-dropdown-name">{user?.full_name}</div>
                    <div className="user-dropdown-email">{user?.email}</div>
                    <div className="user-dropdown-role">{user?.role}</div>
                  </div>
                  <div className="user-dropdown-divider" />
                  <button onClick={logout} className="user-dropdown-logout">
                    Logout
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
