import { apiFetch } from "./client";
import type { ROIInput, ROIResult, ROIScenario } from "../types";

export const calculateROI = (siteId: string, body: ROIInput) =>
  apiFetch<ROIResult>(`/api/v1/sites/${siteId}/roi/calculate`, {
    method: "POST",
    body: JSON.stringify(body)
  });

export const createROIScenario = (siteId: string, body: ROIInput) =>
  apiFetch<{ scenario: ROIScenario; calculation: ROIResult }>(`/api/v1/sites/${siteId}/roi/scenarios`, {
    method: "POST",
    body: JSON.stringify(body)
  });

export const listROIScenarios = (siteId: string) =>
  apiFetch<{ items: ROIScenario[] }>(`/api/v1/sites/${siteId}/roi/scenarios`);

export const getROIScenario = (scenarioId: string) =>
  apiFetch<{ scenario: ROIScenario; calculation: ROIResult }>(`/api/v1/roi/scenarios/${scenarioId}`);

export const deleteROIScenario = (scenarioId: string) =>
  apiFetch<{ status: string }>(`/api/v1/roi/scenarios/${scenarioId}`, {
    method: "DELETE"
  });
