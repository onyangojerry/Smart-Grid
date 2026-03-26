import { apiFetch } from "./client";
import type { OptimizationRun, OptimizationRunBody, OptimizationRunDetail } from "../types";

export const runOptimization = (siteId: string, body: OptimizationRunBody) =>
  apiFetch<OptimizationRun>(`/api/v1/sites/${siteId}/optimize/run`, {
    method: "POST",
    body: JSON.stringify(body)
  });

export const getOptimizationRuns = async (siteId: string) => {
  const response = await apiFetch<{ items: OptimizationRun[] } | OptimizationRun[]>(`/api/v1/sites/${siteId}/optimize/runs`);
  return Array.isArray(response) ? response : response.items;
};

export const getOptimizationRunDetail = (runId: string) =>
  apiFetch<OptimizationRunDetail>(`/api/v1/optimization-runs/${runId}`);
