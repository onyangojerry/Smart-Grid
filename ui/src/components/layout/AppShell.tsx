import React from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import "../../styles/layout.css";

export function AppShell() {
  return (
    <div className="app-shell">
      <div className="main-content">
        <Topbar />
        <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
          <Sidebar />
          <main className="page-container">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
