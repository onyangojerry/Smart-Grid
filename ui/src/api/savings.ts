import { apiFetch } from "./client";
import type { SavingsSummary } from "../types";

export const getSavingsSummary = (siteId: string, from?: string, to?: string) =>
  apiFetch<SavingsSummary>(`/api/v1/sites/${siteId}/savings/summary`, {
    params: {
      ...(from ? { from } : {}),
      ...(to ? { to } : {})
    }
  });
