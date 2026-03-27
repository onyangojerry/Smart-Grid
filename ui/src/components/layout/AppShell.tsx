import React from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import "../../styles/layout.css";

export function AppShell() {
  return (
    <div className="app-shell">
      <Topbar />
      <div className="app-body">
        <Sidebar />
        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
