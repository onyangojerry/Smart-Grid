import React from "react";
import { useRouteError, useNavigate, isRouteErrorResponse } from "react-router-dom";
import { Topbar } from "./Topbar";
import "../../styles/layout.css";

export function ErrorPage() {
  const error = useRouteError();
  const navigate = useNavigate();

  let errorMessage: string;
  let errorStatus: number | string = "Error";

  if (isRouteErrorResponse(error)) {
    errorMessage = error.statusText || error.data?.message || "Page not found";
    errorStatus = error.status;
  } else if (error instanceof Error) {
    errorMessage = error.message;
  } else if (typeof error === "string") {
    errorMessage = error;
  } else {
    console.error(error);
    errorMessage = "An unexpected error occurred.";
  }

  return (
    <div className="app-shell" style={{ flexDirection: "column" }}>
      <Topbar />
      <main className="page-container" style={{ display: "grid", placeItems: "center", minHeight: "calc(100vh - 56px)" }}>
        <div className="error-page-card">
          <div className="error-page-icon">⚠️</div>
          <h1 className="error-page-title">{errorStatus}</h1>
          <p className="error-page-message">{errorMessage}</p>
          {import.meta.env.DEV && error instanceof Error && error.stack && (
            <pre className="error-page-stack">{error.stack}</pre>
          )}
          <div className="error-page-actions">
            <button onClick={() => navigate(-1)} className="btn-secondary">
              ← Go Back
            </button>
            <button onClick={() => navigate("/")} className="btn-primary">
              Return Home
            </button>
          </div>
        </div>
      </main>
      <style>{`
        .error-page-card {
          max-width: 600px;
          width: 100%;
          background: var(--card-bg);
          border: 1px solid var(--border);
          border-radius: 12px;
          padding: 40px;
          text-align: center;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        }
        .error-page-icon {
          font-size: 48px;
          margin-bottom: 20px;
        }
        .error-page-title {
          font-family: var(--syne);
          font-size: 32px;
          font-weight: 800;
          margin: 0 0 12px 0;
          color: var(--error);
        }
        .error-page-message {
          font-size: 18px;
          color: var(--text);
          margin-bottom: 30px;
          line-height: 1.6;
        }
        .error-page-stack {
          text-align: left;
          background: rgba(0,0,0,0.05);
          padding: 16px;
          border-radius: 8px;
          font-size: 12px;
          font-family: var(--mono);
          overflow-x: auto;
          margin-bottom: 30px;
          max-height: 200px;
          border: 1px solid var(--border);
        }
        .error-page-actions {
          display: flex;
          gap: 12px;
          justify-content: center;
        }
      `}</style>
    </div>
  );
}
