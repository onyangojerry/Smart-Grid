import React from "react";
import { useNavigate, useRouteError } from "react-router-dom";

export function ErrorPage() {
  const error = useRouteError() as any; // Type assertion for simplicity; in a real app, you'd want a more robust type
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate("/");
  };

  const containerStyle: React.CSSProperties = {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "100vh",
    backgroundColor: "#f8f9fa", /* Light background */
    color: "#333",
    textAlign: "center",
    padding: "20px",
    boxSizing: "border-box",
  };

  const contentStyle: React.CSSProperties = {
    maxWidth: "600px",
    backgroundColor: "#ffffff",
    padding: "40px",
    borderRadius: "8px",
    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
  };

  const titleStyle: React.CSSProperties = {
    fontSize: "2.5em",
    marginBottom: "15px",
    color: "#dc3545", /* Red for error */
  };

  const messageStyle: React.CSSProperties = {
    fontSize: "1.2em",
    marginBottom: "10px",
  };

  const detailsStyle: React.CSSProperties = {
    fontSize: "0.9em",
    color: "#6c757d", /* Muted text for details */
    marginBottom: "30px",
  };

  const buttonStyle: React.CSSProperties = {
    padding: "12px 25px",
    fontSize: "1em",
    borderRadius: "5px",
    cursor: "pointer",
    transition: "background-color 0.3s ease",
    backgroundColor: "#007bff", /* Primary blue */
    color: "white",
    border: "none",
  };

  return (
    <div style={containerStyle}>
      <div style={contentStyle}>
        <h1 style={titleStyle}>Oops! Something went wrong.</h1>
        <p style={messageStyle}>
          {error?.statusText || error?.message || "An unexpected error occurred."}
        </p>
        <p style={detailsStyle}>
          {error?.status && `Status: ${error.status}`}
        </p>
        <button onClick={handleGoHome} style={buttonStyle}>
          Go back to Homepage
        </button>
      </div>
    </div>
  );
}
