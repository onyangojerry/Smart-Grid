import { apiFetch } from "./client";
import type { Alert, AlertCreateBody, AlertCount } from "../types";

export const createAlert = (siteId: string, body: AlertCreateBody) =>
  apiFetch<Alert>(`/api/v1/sites/${siteId}/alerts`, {
    method: "POST",
    body: JSON.stringify(body)
  });

export const getAlerts = (siteId: string, state?: string, limit = 100) =>
  apiFetch<{ items: Alert[] }>(`/api/v1/sites/${siteId}/alerts`, {
    params: { state: state ?? "", limit: String(limit) }
  });

export const getAlertCounts = (siteId: string) =>
  apiFetch<AlertCount>(`/api/v1/sites/${siteId}/alerts/count`);

export const getAlert = (alertId: string) =>
  apiFetch<Alert>(`/api/v1/alerts/${alertId}`);

export const acknowledgeAlert = (alertId: string) =>
  apiFetch<Alert>(`/api/v1/alerts/${alertId}/acknowledge`, {
    method: "PATCH"
  });

export const resolveAlert = (alertId: string) =>
  apiFetch<Alert>(`/api/v1/alerts/${alertId}/resolve`, {
    method: "PATCH"
  });
