import React from "react";
import { Navigate, createBrowserRouter } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import { RequireAuth, useAuth } from "../features/auth/useAuth";
import { LoginPage } from "../features/auth/LoginPage";
import { SignupPage } from "../features/auth/SignupPage";
import { WelcomePage } from "../features/public/WelcomePage";
import { SitesPage } from "../features/sites/SitesPage";
import { SiteDetailPage } from "../features/sites/SiteDetailPage";
import { DevicesPage } from "../features/devices/DevicesPage";
import { TelemetryPage } from "../features/telemetry/TelemetryPage";
import { OptimizationPage } from "../features/optimization/OptimizationPage";
import { CommandsPage } from "../features/commands/CommandsPage";
import { SavingsPage } from "../features/savings/SavingsPage";
import { SimulationPage } from "../features/simulation/SimulationPage";
import { AlertsPage } from "../features/alerts/AlertsPage";
import { ROIPage } from "../features/roi/ROIPage";
import { SettingsPage } from "../features/settings/SettingsPage";
import { UsersPage } from "../features/users/UsersPage";
import { ErrorPage } from "../components/layout/ErrorPage";

function HomeRoute() {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/sites" replace />;
  return <WelcomePage />;
}

export const router = createBrowserRouter([
  { 
    path: "/", 
    element: <HomeRoute />,
    errorElement: <ErrorPage />
  },
  { path: "/login", element: <LoginPage />, errorElement: <ErrorPage /> },
  { path: "/signup", element: <SignupPage />, errorElement: <ErrorPage /> },
  {
    path: "/",
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    errorElement: <ErrorPage />,
    children: [
      { path: "sites", element: <SitesPage /> },
      { path: "sites/:siteId", element: <SiteDetailPage /> },
      { path: "sites/:siteId/devices", element: <DevicesPage /> },
      { path: "sites/:siteId/telemetry", element: <TelemetryPage /> },
      { path: "sites/:siteId/optimization", element: <OptimizationPage /> },
      { path: "sites/:siteId/commands", element: <CommandsPage /> },
      { path: "sites/:siteId/savings", element: <SavingsPage /> },
      { path: "sites/:siteId/simulation", element: <SimulationPage /> },
      { path: "sites/:siteId/alerts", element: <AlertsPage /> },
      { path: "sites/:siteId/roi", element: <ROIPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "admin/users", element: <UsersPage /> }
    ]
  }
]);
