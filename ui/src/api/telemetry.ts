import { apiFetch } from "./client";
import type { TelemetryIngestBody, TelemetryIngestResponse } from "../types";

export const ingestTelemetry = (body: TelemetryIngestBody) =>
  apiFetch<TelemetryIngestResponse>("/api/v1/telemetry/ingest", {
    method: "POST",
    body: JSON.stringify(body)
  });

export const getTelemetryLatest = (siteId: string) =>
  apiFetch<Record<string, { value: number; unit: string; ts: string; quality: "good" | "estimated" | "bad" }>>(
    `/api/v1/sites/${siteId}/telemetry/latest`
  );

export const getTelemetryHistory = (siteId: string, key: string, from: string, to: string) =>
  apiFetch<Array<{ canonical_key: string; ts: string; value: number; unit: string; quality: "good" | "estimated" | "bad" }>>(
    `/api/v1/sites/${siteId}/telemetry/history`,
    { params: { key, from, to } }
  );

