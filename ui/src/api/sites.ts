import { apiFetch } from "./client";
import type { Site, SiteCreateBody, SiteDashboard } from "../types";

export const getSites = async () => {
  const response = await apiFetch<{ items: Site[] } | Site[]>("/api/v1/sites");
  return Array.isArray(response) ? response : response.items;
};

export const getSite = (siteId: string) => apiFetch<Site>(`/api/v1/sites/${siteId}`);

export const createSite = (body: SiteCreateBody) =>
  apiFetch<Site>("/api/v1/sites", {
    method: "POST",
    body: JSON.stringify(body)
  });

export const patchSite = (siteId: string, body: Partial<Record<string, unknown>>) =>
  apiFetch<Site>(`/api/v1/sites/${siteId}`, {
    method: "PATCH",
    body: JSON.stringify(body)
  });

export const getSiteDashboard = (siteId: string) =>
  apiFetch<SiteDashboard>(`/api/v1/sites/${siteId}/dashboard`);
