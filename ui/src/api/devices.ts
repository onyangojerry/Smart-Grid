import { apiFetch } from "./client";
import type { Device, DeviceCreateBody } from "../types";

export const createSiteDevice = (siteId: string, body: DeviceCreateBody) =>
  apiFetch<Device>(`/api/v1/sites/${siteId}/devices`, {
    method: "POST",
    body: JSON.stringify(body)
  });

export const getSiteDevices = (site_id: string) => apiFetch<Device[]>(`/api/v1/sites/${site_id}/devices`);

export const getSiteAssets = (siteId: string) =>
  apiFetch<Array<{ id: string; site_id: string; asset_type: string; name: string; created_at: string }>>(
    `/api/v1/sites/${siteId}/assets`
  );

export const getAsset = (assetId: string) =>
  apiFetch<{ id: string; site_id: string; asset_type: string; name: string; created_at: string }>(
    `/api/v1/assets/${assetId}`
  );

export const deleteAsset = (assetId: string) =>
  apiFetch<void>(`/api/v1/assets/${assetId}`, { method: "DELETE" });

export const createAsset = (siteId: string, body: Record<string, unknown>) =>

  apiFetch<Record<string, unknown>>(`/api/v1/sites/${siteId}/assets`, {
    method: "POST",
    body: JSON.stringify(body)
  });

export const createAssetDevice = (assetId: string, body: Record<string, unknown>) =>
  apiFetch<Record<string, unknown>>(`/api/v1/assets/${assetId}/devices`, {
    method: "POST",
    body: JSON.stringify(body)
  });

export const createDeviceMapping = (deviceId: string, body: Record<string, unknown>) =>
  apiFetch<Record<string, unknown>>(`/api/v1/devices/${deviceId}/mappings`, {
    method: "POST",
    body: JSON.stringify(body)
  });
